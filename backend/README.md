# Nya-AI backend

All Python for Nya-AI in one uv project and one package, `app`: the FastAPI API, the law library
(RAG) and the LangGraph agents. One `pyproject.toml`, one `uv.lock`, one `.venv`, one `.env`.

```
backend/
  pyproject.toml, uv.lock, .env.example
  Dockerfile             API image
  docker-compose.yml     Postgres + pgvector (5433) and self-hosted Langfuse (3000)
  app/
    main.py              FastAPI app: CORS, routers, startup seed
    cli.py               `uv run nya-agent ...`: fetch, count, setup, ingest, golden, search, status, ask, answers, slo
    api/
      routers/           HTTP only: auth, chat, lawyers, bookings, payments, dashboard, messages, support,
                         reviews (advocate queue), agent (/v1)
      schemas/           request and response models, one module per router: the API contract
    core/
      config.py          settings for the API and the agents, from .env
      paths.py           data/, data/raw/ and section_map.csv, defined once
      security.py        JWT, OTP and guest login
      observability.py   Langfuse client and PII masking
    db/                  app database (SQLite in dev): session.py, models.py, seed.py
    services/            business rules the routers call; raise errors.py exceptions, not HTTP ones
      bookings.py, payments.py (Razorpay), dashboard.py, lawyers.py
      agent.py           runs agent turns for chat and /v1, queues advocate reviews, writes audit_log
      chat_engine.py     keyword rule engine: the basic-mode fallback
    agents/              R1: graph.py (LangGraph nodes and wiring), runner.py (checkpoints, Langfuse, stream,
                         resume), sql_agent.py, guards.py, triage.py, safety_llm.py, llm.py (Azure)
    rag/                 law library: parser, ingest, index (pgvector), retrieve (hybrid), acts, tables (SQL tables)
    evals/               golden-set check; Ragas and SLO scores next (../docs/SLOS.md)
  data/                  SOURCES.md, section_map.csv; PDFs go in data/raw/ (not committed)
  docker/db-init.sql     creates the extra databases for Langfuse and tests
  tests/
    api/                 booking brief, payments signature, support, service routes
    rag/                 parser and dates offline; ingest and retrieval against Postgres
```

## Run the API

```bash
cd backend
uv sync
cp .env.example .env            # optional for the API; defaults work with zero configuration
uv run uvicorn app.main:app --reload --port 8000
```

The API is at `http://localhost:8000/api`, docs at `http://localhost:8000/docs`. A local
`nya_ai.db` SQLite file is created and seeded on first boot. Chat answers come from the R1 agent graph
(`app/agents/graph.py`). When the law library (Postgres) isn't reachable, ordinary questions fall back to
the keyword rule engine ("basic mode", `meta.mode = "basic"`). Emergencies and refusals still come from
the agent's rules. The agent is also exposed on its own at `/v1/answer`, `/v1/answer/stream` (server-sent
events, one per graph node), `/v1/review` and `/v1/health`. Advocates work the review queue at
`/api/reviews`. Payments use Razorpay test keys;
without them the payment endpoints return `503`.

## Law library

```bash
cd backend
docker compose up -d            # Postgres + pgvector on 5433, Langfuse on http://localhost:3000
# put your Azure endpoint and key in .env
uv run nya-agent setup          # tables, acts, section map
uv run nya-agent fetch          # the four India Code PDFs into data/raw/ (see data/SOURCES.md)
uv run nya-agent count          # check section counts; no database or Azure needed
uv run nya-agent ingest         # BNS BNSS BSA IPC
uv run nya-agent golden ../../legal-docs-platform/evals/GOLDEN-QUERIES.md
uv run nya-agent search "My phone was stolen in March 2024" --as-of 2024-03-12
uv run nya-agent status
uv run nya-agent ask "Which BNS section replaced IPC 420?"   # one question through the graph, with its trace
uv run nya-agent answers --out run.jsonl                     # golden + holdout answers for `slo --answers`
```

What the library does: one node per section (`SectionNodeParser`, explanations and illustrations
kept with their section); Azure `text-embedding-3-large` at 1536 dimensions into pgvector with a
full-text column through a LlamaIndex `IngestionPipeline` (unchanged acts are not re-embedded);
hybrid retrieval fusing vector and full-text search after filtering to the acts in force on the
date (IPC before 1 July 2024; BNS, BNSS and BSA from then); SQL tables `acts`, `sections`,
`section_map`, `offence_class`, `ingestion_jobs`; every ingestion run traced in Langfuse.

Expected section counts: BNS 358, BNSS 531, BSA 170, IPC 511 numbered sections. Langfuse login on
first start: `admin@nya.local` / `change-me-admin` (change the values in `docker-compose.yml`).

## Tests and static analysis

```bash
uv run pytest
uv run ruff check .          # lint (rules in pyproject.toml)
uv run ruff format --check .  # formatting, 120 columns
uv run pylint app             # 10.00/10 on 2026-11-01
```

The Postgres tests ingest a synthetic fixture with a mock embedding into the `nya_test` database and
are skipped when the database is not running. No Azure key is needed for tests.

## Notes

- uv only: add dependencies with `uv add <pkg>` (`uv add --group dev <pkg>` for dev tools).
- Two LlamaIndex workarounds are noted in `app/rag/index.py` (docstore built from the kvstore;
  psycopg2 for the vector store).
- Product decisions are in `../docs/DECISIONS.md`; SLO definitions in `../docs/SLOS.md`.
