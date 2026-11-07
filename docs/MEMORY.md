# Nya-AI memory management

What the agent remembers, where it is kept, for how long, and what is never kept. Sprint task 18.

## Three kinds of memory

| Kind | What it holds | Where | Lifetime | Code |
|---|---|---|---|---|
| **Short-term (graph state)** | One turn's working state: redacted question, route, risk, acts in force, retrieved sections, SQL result, draft, critique, the advocate's decision | LangGraph checkpointer: Postgres (`CHECKPOINT_DATABASE_URL`), SQLite fallback (`CHECKPOINT_DB`), in-memory in tests | One turn, or until an advocate decides on a held answer | `app/agents/runner.py`, `app/agents/state.py` |
| **Conversation (long-term)** | The chat transcript per conversation: user and AI messages, citations, the agent's meta (route, trace id, review id), the incident date | App database, `chat_messages` | Until the user deletes the conversation (see Retention) | `app/db/models.py`, `app/services/agent.py` |
| **Matters (long-term)** | The incident timeline and deadline clocks on the dashboard, derived from `chat_messages.incident_date` | App database (computed, not stored separately) | As the chat rows | `app/services/deadlines.py`, `GET /api/chat/matters` |

The law library (acts, sections, vectors, section map) is reference data, not memory: it holds
nothing about users.

## How a turn uses memory

1. Each turn runs on a **new thread id** (`uuid4`), so graph state never leaks from one turn or one
   user into another. The thread id is stored on the AI message and on `answer_reviews`.
2. Conversation context comes from the app database: the last 6 messages of the conversation are
   loaded (`_history`) and the writer sees the last 4, each **PII-redacted** and cut to 400 characters.
3. The graph checkpoints after every node. If the answer needs an advocate (a live matter), the graph
   `interrupt()`s; the checkpoint keeps the draft until the advocate approves, edits or rejects it in
   the review queue, and `resume()` continues the same thread, even after an API restart.

Why per-turn threads instead of thread = conversation: the graph state is built for one question (one
evidence set, one draft, one critique). Carrying it across turns would mix evidence from different
questions. The conversation itself already lives in `chat_messages`, which the user can see and delete.

## Storage

- **Postgres** (default on the owner's machine): the local Postgres 16 on port 9000, database `nya-ai`,
  the same database as the law library. `PostgresSaver` creates `checkpoints`, `checkpoint_blobs`,
  `checkpoint_writes` and `checkpoint_migrations` on first start. A small connection pool (1 to 5).
- **SQLite fallback**: if `CHECKPOINT_DATABASE_URL` is empty or Postgres is down when the API starts,
  the runner logs a warning and uses `nya_graph.db`, so chat keeps working.
- **Tests**: in-memory (`memory_checkpointer()`); `tests/agents/test_checkpointer_pg.py` proves a held
  answer resumes after a restart on Postgres, and the SQLite fallback.
- Checkpoints only load the agent's own Pydantic types (`STATE_TYPES` in the serializer), so a
  tampered checkpoint cannot make the loader build arbitrary objects.

## What is never stored or sent

- **Never sent to a model or a trace**: the raw question (`state.question`) and raw history. Models
  see `redacted_question` and redacted history; Aadhaar, PAN, phone numbers and emails are replaced
  by labels (`app/agents/guards.py`). Langfuse masks the same patterns again on export
  (`app/core/observability.py`) and sees a hash of the user id, never the phone number.
- **Never given to the model as memory or a tool**: other users' conversations, bookings, briefs or
  payments. These are reached only by the FastAPI services under login and permissions
  (`docs/DECISIONS.md`, "Data access: MCP for law data only").
- **Not stored at all**: payment card details (Razorpay holds them), OTPs, call audio.
- **Stored but internal**: the checkpoint keeps `state.question` as typed, so a resumed review shows
  the advocate the real question. The checkpoint tables sit in the same protected database as the
  chat rows and are never exposed through an API.

## Retention and DPDP

Under the Digital Personal Data Protection Act 2023 the purpose is answering the user's legal-
information question and, when asked, preparing a consultation. Proposed retention (not yet automated):

| Data | Keep | Then |
|---|---|---|
| Checkpoints of finished turns | 30 days (for debugging and audit replay) | Delete |
| Checkpoints of answers waiting for review | Until decided, at most 14 days | Expire the review, delete |
| `chat_messages` | While the account exists | Deleted with the conversation or the account |
| Langfuse traces | 30 days (masked, user id hashed) | Langfuse retention setting |
| `audit_log` | 1 year | Archive |

Open items: a scheduled prune for checkpoints and expired reviews, and a "delete my conversations"
endpoint that also removes the turn's checkpoints by thread id.

## Configuration

```
CHECKPOINT_DATABASE_URL=postgresql://subash@localhost:9000/nya-ai   # empty = SQLite
CHECKPOINT_DB=./nya_graph.db                                         # SQLite fallback
```
