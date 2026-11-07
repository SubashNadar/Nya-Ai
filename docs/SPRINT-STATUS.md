# Sprint status (capstone tasks 1–22)

As of 7 November 2026. "LDP" is the design repo, SubashNadar/legal-docs-platform; every other path is in
this repo.

| Sprint | Task | Deliverable | Status | Evidence |
|---|---|---|---|---|
| 1 | 1 | Project Approach Document | Done | LDP `docs/PLAN.md`, `docs/NYA-AI.md` |
| 1 | 2 | Use Case & Success Definition | Done | LDP `docs/USE-CASES.md` |
| 1 | 3 | Initial System Blueprint | Done | LDP `docs/ARCHITECTURE.md`, `docs/TECHNOLOGY.md` |
| 1 | 4 | Evaluation & Measurement Plan | Done | LDP `docs/VERIFICATION.md`; `docs/SLOS.md` |
| 1 | 5 | Project Setup Readiness | Done | `backend/README.md` (uv, Docker, local Postgres 16 + pgvector, Azure); CLAUDE.md log 2026-11-07 |
| 2 | 6 | High Level Architecture Diagram | Done | `docs/diagrams/architecture-detailed.*` (`draw_v12.py`) |
| 2 | 7 | ADR (Architecture Decision Record) | Done | `docs/adr/` (11 ADRs); running log `docs/DECISIONS.md` |
| 2 | 8 | Project Dashboard Creation (Miro/Trello) | **Link needed from owner** | Add the board link here and in the README |
| 3 | 9 | Detailed Use Case Specification & SLO Definition | Done | `docs/SLOS.md`, `evals/slo-test-sheet.xlsx` (16-metric matrix) |
| 3 | 10 | Detailed Solution Design | Done | LDP `docs/ARCHITECTURE.md`, `docs/AGENTS-TOOLS-SEARCH.md`; `backend/app/agents/graph.py`; ADRs 0001–0004 |
| 3 | 11 | Query Categories Definition | Done | Routes rag / sql / hybrid / none and risk levels in `backend/app/agents/triage.py` and the `triage` prompt; labels in `evals/cases/*.json` |
| 3 | 12 | Evaluation Dataset & Test Strategy | Done | `evals/cases/` golden 50, holdout 45 (frozen), SQL 21, stress 30 (frozen); `docs/SLOS.md` "Test cases" |
| 3 | 13 | Prompt Engineering Framework | Done | `docs/PROMPTS.md`; `backend/app/agents/prompts/`; `tests/agents/test_prompts.py` |
| 3 | 14 | FastAPI Service Setup | Done | `backend/app/main.py`; `/api/*`, `/v1/answer`, `/v1/answer/stream`, `/v1/review`, `/v1/health` |
| 4 | 15 | Golden Dataset Ready | Done | LDP `evals/GOLDEN-QUERIES.md`; `evals/cases/golden.json` |
| 4 | 16 | Vector DB Indexed & Retrieval Validated | Done | BNS 358, BNSS 531, BSA 170, IPC 511 (+44 lettered) sections, 1,671 nodes in pgvector; golden check PASS (23/23). Known: ranking needs tuning for broad questions |
| 4 | 17 | SQL Schema Deployed with Scaled Data | **Partial** | Schema deployed (`backend/app/rag/tables.py`); `sections` 1,614 rows. `section_map` has 10 rows until the official BPR&D IPC→BNS table is loaded (download needs the owner's browser) |
| 4 | 18 | Memory Management Strategy Finalized | Done | `docs/MEMORY.md`; ADR 0005; Postgres checkpointer in `backend/app/agents/runner.py` |
| 4 | 19 | MCP / Tool Integration Configured | Done | `backend/app/agents/mcp_server.py` (6 tools, stdio + HTTP, `nya-agent mcp`), `mcp_client.py`; ADR 0004 |
| 4 | 20 | Logging & Tracing Operational | Done | Self-hosted Langfuse (:3000): graph runs, ingestion, every Azure call; ADR 0008 |
| 4 | 21 | Baseline Metrics Captured (TSR, Latency, Grounding) | **Owner checking manually** | Tooling ready: `nya-agent answers` then `nya-agent slo --answers` |
| 4 | 22 | Cost Tracking / Observability Enabled | Done | `backend/app/core/costs.py`, `nya-agent cost`; prices in `.env` are placeholders until the owner fills them in |

## Open items

- Task 8: the owner adds the Miro/Trello board link.
- Task 17: save the BPR&D table PDF to `backend/data/raw/bprd_bns_ipc_comparison.pdf`, then build
  `section_map.csv` from it.
- Task 21: the owner runs and checks the baseline.
- Task 22: fill in the `PRICE_*` values in `backend/.env` from the Azure pricing page, then run
  `nya-agent cost --register-prices`.
- Retrieval ranking for broad questions (task 16 follow-up); checkpoint retention automation (task 18
  follow-up).
