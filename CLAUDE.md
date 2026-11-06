# Nya-AI — project memory

Read this first in any new session and keep it current.

## What this is

**Nya-AI** is an AI legal-information app for India: free cited answers from Indian bare acts and
judgments, plus paid consultations with verified advocates (₹500, advocate keeps 70%). It was
previously built under another name; that name and its design files were removed on 2026-10-29.
Nya-AI is the only product.

## Sources of truth

1. **UI:** layouts from the Orbit design canvas, https://claude.ai/artifact/QYs5pGyrFcvACgYUWrUp1g
   (every screen has a desktop and a phone board, wired for Play mode). Keep Orbit's menu, layout
   and alignment exactly. Colours are **Orbit navy and brass** again since 2026-11-06 (Sage & Clay was
   used 2026-10-30 to 2026-11-06; see `docs/DESIGN.md`). Fraunces headings, Figtree body, JetBrains
   Mono for metadata and citations. Since 2026-11-06 the menu is the Orbit Dial (logo orb) and the
   dashboard is the incident timeline with deadline clocks (owner's choice; see `docs/DESIGN.md`). Tokens live in `frontend/tailwind.config.js`. New control styling or behaviour needs the owner's approval first (proposals in
   `docs/DESIGN.md`).
2. **Agent plan:** https://claude.ai/artifact/KtuTmzcwCe2aMQqWRtVN29 (LangGraph graph, LlamaIndex
   library, Langfuse observability, per-agent SLOs).
3. **Capstone design:** SubashNadar/legal-docs-platform `docs/NYA-AI.md` and
   `evals/GOLDEN-QUERIES.md`.
4. **API contract:** `backend/app/api/schemas/` (one module per router) + `routers/`, mirrored by
   `frontend/src/types.ts` + `lib/api.ts`. If they disagree, that is a bug.
5. **Decisions:** `docs/DECISIONS.md`.
6. **SLOs:** `docs/SLOS.md` (definitions, targets, guardrails, how they are tested) and
   `evals/slo-test-sheet.xlsx` (50 golden queries + 10 SLO probes, charts). Keep them in step.

## Where the code lives

- `backend/` — one uv project, one package `app` (`backend/pyproject.toml`, one `uv.lock`, one
  `.venv`, one `.env`). See `backend/README.md`. Run: `cd backend && uv sync && uv run uvicorn
  app.main:app --reload --port 8000`. SQLite dev DB `nya_ai.db` is created and seeded on boot. Docker:
  `cd backend && docker build -t nya-ai-api .`.
  - `app/api/` routers + schemas, `app/core/` settings, security, Langfuse, `app/db/` models and seed,
    `app/services/` chat rule engine.
  - `app/rag/` — law library (R0 built): section parser, LlamaIndex ingestion into pgvector, hybrid
    retrieval with act/date filters, SQL tables. CLI `uv run nya-agent ...` (`app/cli.py`).
    `docker compose up -d` in `backend/` starts pgvector (5433) and Langfuse (3000). PDFs go in
    `backend/data/raw/` (gitignored).
  - `app/agents/` — guardrails, triage, model safety layer and the R1 LangGraph graph (`graph.py`,
    `runner.py`, `sql_agent.py`). Chat calls it through `app/services/agent.py`; `/v1/*` exposes it;
    `/api/reviews` is the advocate queue; `audit_log` is the governance record.
    `app/evals/` — golden check, SLO runner (`nya-agent slo`), RBAC probes, Ragas and judge scoring.
- `frontend/` — Vite + React + TypeScript + Tailwind 3 (shadcn/ui pattern, lucide, motion, sonner).
  Run: `cd frontend && npm install && npm run dev`.

## Conventions

- **uv only** for Python.
- Push straight to `main`; run `npm run build` and, in `backend/`, `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .` and `uv run pylint app` first.
- OTP login accepts any 4-digit code. Payments are real Razorpay (test keys), payouts manual.
- Public legal sources only; never advice on a user's own case; escalate to an advocate.
- Azure OpenAI (personal subscription): gpt-5.4-nano, gpt-5.4, text-embedding-3-large at 1536
  dimensions. Keys never committed.

## Log (newest first)

- **2026-11-06** — Orbit Dial menu + Statute Timeline (owner picked from three concepts). Sidebar and
  phone tab bar replaced by the logo orb menu (`OrbMenu.tsx`). `/dashboard` is now "My matters":
  incident timeline across 1 July 2024 and deadline clocks. Chat sends `incident_date` (agent
  temporal node uses it). New `GET /api/chat/matters`, `chat_messages.incident_date`,
  `app/services/deadlines.py` (NI Act 138(b), RTI 19(1), Consumer Act 69, Limitation Act money claims).

- **2026-11-06** — Motion and controls kit at the owner's request ("trendy controls and animations"):
  spotlight/tilt cards, ripple and glowing buttons, sliding pills, route transitions, staggered lists,
  count-up stats, composer border beam, skeleton loading. Layout unchanged; reduced motion respected.
  See `docs/DESIGN.md`.

- **2026-11-06** — The owner chose to restore the Orbit navy and brass colours, replacing Sage & Clay.
  The frontend theme commits d12d908 and f19d7b8 were reversed; only colours changed, not the layout.

- **2026-11-06** — R1 agent built (`app/agents/graph.py`): guard, temporal, router, statute
  researcher and SQL agent in parallel for hybrid, writer, critic with one retry, advocate review with
  `interrupt()`. `/api/chat/message` now answers from it, with the rule engine as basic mode when the
  library is down. Added `/v1/answer`, `/v1/answer/stream` (SSE), `/v1/review`, `/v1/health`, the
  review queue `/api/reviews`, the `audit_log` and `answer_reviews` tables, `chat_messages.meta_json`,
  and the `nya-agent ask` and `answers` commands. Tested offline with fake tools only: there is no real
  ingestion or Azure run yet. See `docs/DECISIONS.md`.
- **2026-11-06** — Remaining planned endpoints: `POST /api/chat/feedback` (thumbs/report, Langfuse
  `user_feedback`, unsafe reports audited), `POST /api/plan/draft` (consult planner, rules or nano),
  `GET /api/library/acts` and `POST /api/library/ingest` (advocate accounts; checks PDFs, Azure, DB).
  Lawyer portal now shows "Answers waiting for review" (owner approved). Chat thumbs and plan prefill
  are in `lib/api.ts` but not yet on screen.

- **2026-11-03** — Validated against the course's 16-metric SLO matrix (`docs/SLOS.md`, "SLO matrix"
  sheet, `uv run nya-agent slo`). Built input/output guardrails (`app/agents/guards.py`), rule triage
  for risk/route/escalation (`app/agents/triage.py`), an Azure nano safety layer OR-ed with the rules
  (`safety_llm.py`, not yet run), parameterized SQL templates (`app/rag/sql_queries.py`), RBAC probes,
  and the Ragas/judge/Langfuse scoring (`app/evals/slo.py`). Measured: RBAC 0 violations (after fixing
  a chat-history cross-account leak), SQL 80%, safety/routing 65–73% on unseen questions (rules
  generalise badly). Metrics 1–8 and 10 wait for the R1 agent and the Azure key. Case sets in
  `evals/cases/` (holdout and stress are frozen).

- **2026-11-01** — Backend tidy-up: `app/rag/db.py` renamed `app/rag/tables.py`; data paths live in
  `app/core/paths.py`; `app/api/schemas.py` split into `app/api/schemas/` per router; booking,
  payment, dashboard and lawyer-card logic moved to `app/services/` (routers are HTTP only; services
  raise `app/services/errors.py`, mapped to `{"detail"}` responses in `main.py`). Architecture diagram
  and pitch deck reworked from the owner's 10-point feedback.

- **2026-10-30** — Theme changed from Orbit navy/brass to Sage & Clay (light, calmer) after the owner
  found Orbit too aggressive. Only colours changed; Orbit menu and layout untouched. The first push
  (d12d908) also restyled controls; the owner asked to keep layout and approve controls first, so
  those were removed and listed as proposals in `docs/DESIGN.md`. No dark mode yet.

- **2026-10-30** — Backend restructured into one package `app` by layer (api, core, db, services,
  agents, rag, evals), tests in `backend/tests/{api,rag}`, one `.env` (agent Postgres URL renamed
  `VECTOR_DATABASE_URL`). No more `nya_ai`/`nya_agent` packages or `backend/api`, `backend/agent`.
  The GitHub repo is now SubashNadar/Nya-Ai (renamed from Neethi-X).

- **2026-10-30** — SLO definitions and targets in `docs/SLOS.md` and the test sheet
  `evals/slo-test-sheet.xlsx`, following the evaluation rules: Ruff/pylint, input and output
  guardrails, every SLO defined, scores pushed to Langfuse, SLO test cases, Excel plots, Ragas. None
  of it is in code yet.

- **2026-10-30** — Repo layout: all Python moved under `backend/` as one uv workspace, the API to
  `backend/api/`, the agent (was `nya-ai/`) to `backend/agent/`; Python 3.12 for both. Section
  parser checked on the real acts: BNS 358, BNSS 531 and BSA 170 all found. The IPC count hung on
  runs of blank lines; fixed in 49f60d3, its count is not yet confirmed. BNS, BNSS and BSA now come
  from indiacode.gov.in (the old indiacode.nic.in links return 504); the IPC still comes from
  indiacode.nic.in.
- **2026-10-29** — Agent service R0 (law library) in `nya-ai/`. Tested on a synthetic fixture
  against real pgvector and a running Langfuse; not yet run on the real acts because India Code is
  blocked from cloud sessions and the Azure key lives only on the owner's machine. Golden check
  currently FAILs as expected (nothing real ingested). Next: real PDFs + Azure, then R1 (graph).
- **2026-10-29** — Consult plan (`/plan`) and call room (`/call/:bookingId`). "Ask an advocate" in
  chat opens the plan with the question as the facts; the plan is sent as `brief` with
  `POST /api/bookings` (stored in `bookings.brief_json`, added to old dev DBs on boot) and shown to
  the advocate in the portal and the call room. In-app video is not wired; the call room says the
  advocate phones the client and offers agenda, brief and on-device notes. Law library admin waits
  for the agent's ingestion pipeline. Fixed tab highlighting (`/bookings` also lit Lawyers).
- **2026-10-29** — Public Legal, About, Contact and Help pages (`/legal`, `/about`, `/contact`,
  `/help`, shared `InfoLayout`, no sign-in needed), linked from sign-in, sidebar and Account. Contact
  form posts to `POST /api/support` (`SupportMessage`, refs `SUP-YYYYMMDD-###`). Placeholders such
  as [SUPPORT EMAIL] and [OFFICER NAME] still need real values.
- **2026-10-29** — Orbit theme applied across the app (tokens in `tailwind.config.js`, grid in
  `index.css`); chat rebuilt to the Orbit layout (trace panel, cited ¶ answer, temporal panel).
  Orbit screens not yet in the app: law library admin, consult plan, live call, basics states board.
- **2026-10-29** — Rebranded to Nya-AI: package `neethi` → `nya_ai`, Orbit logo and favicon,
  JetBrains Mono added, all user-facing copy renamed. Removed the old design export, UI reference,
  build guardrails, open-questions log, three old subagents, pitch deck, roadmap and Vite template
  leftovers. Key decisions kept in `docs/DECISIONS.md`. Next: build the Orbit screens and the
  `nya-ai/` agent service. The GitHub repo is still named Neethi-X until the owner renames it.
- **2026-10-28** — UI polish and premium navy/brass redesign; Orbit chosen as the final UI.
- **2026-07-18** — Real Razorpay integration; lawyer OTP role login; JWT logout revocation;
  explicit mark-read for messages; standalone mobile Bookings and Account screens.
- **2026-07-17** — Backend and frontend first built and verified end to end.
