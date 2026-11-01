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
    cli.py               `uv run nya-agent ...`: fetch, count, setup, ingest, golden, search, status
    api/
      routers/           HTTP only: auth, chat, lawyers, bookings, payments, dashboard, messages, support
      schemas/           request and response models, one module per router: the API contract
    core/
      config.py          settings for the API and the agents, from .env
      paths.py           data/, data/raw/ and section_map.csv, defined once
      security.py        JWT, OTP and guest login
      observability.py   Langfuse client and PII masking
    db/                  app database (SQLite in dev): session.py, models.py, seed.py
    services/            business rules the routers call; raise errors.py exceptions, not HTTP ones
      bookings.py, payments.py (Razorpay), dashboard.py, lawyers.py
      chat_engine.py     keyword rule engine, the fallback until the agents answer
    agents/              LangGraph graph and its nodes (release R1)
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
`nya_ai.db` SQLite file is created and seeded on first boot. Chat answers come from the keyword rule
engine until the agents in `app/agents/` replace `chat_engine.get_answer`; with `ANTHROPIC_API_KEY`
set it calls the Claude API and falls back to the rules on error. Payments use Razorpay test keys;
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
```

What the library does: one node per section (`SectionNodeParser`, explanations and illustrations
kept with their section); Azure `text-embedding-3-large` at 1536 dimensions into pgvector with a
full-text column through a LlamaIndex `IngestionPipeline` (unchanged acts are not re-embedded);
hybrid retrieval fusing vector and full-text search after filtering to the acts in force on the
date (IPC before 1 July 2024; BNS, BNSS and BSA from then); SQL tables `acts`, `sections`,
`section_map`, `offence_class`, `ingestion_jobs`; every ingestion run traced in Langfuse.

Expected section counts: BNS 358, BNSS 531, BSA 170, IPC 511 numbered sections. Langfuse login on
first start: `admin@nya.local` / `change-me-admin` (change the values in `docker-compose.yml`).

## Tests

```bash
uv run pytest
```

The Postgres tests ingest a synthetic fixture with a mock embedding into the `nya_test` database and
are skipped when the database is not running. No Azure key is needed for tests.

## Notes

- uv only: add dependencies with `uv add <pkg>` (`uv add --group dev <pkg>` for dev tools).
- Two LlamaIndex workarounds are noted in `app/rag/index.py` (docstore built from the kvstore;
  psycopg2 for the vector store).
- Product decisions are in `../docs/DECISIONS.md`; SLO definitions in `../docs/SLOS.md`.
