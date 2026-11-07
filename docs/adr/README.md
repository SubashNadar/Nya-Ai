# Architecture Decision Records

Each record follows Context / Decision / Consequences / Status. Smaller product decisions (themes,
copy, screen behaviour) stay in the running log, [`../DECISIONS.md`](../DECISIONS.md).

| ADR | Title | Date | Status |
|---|---|---|---|
| [0001](0001-one-fastapi-service-with-the-agent-in-process.md) | One FastAPI service with the agent in process | 2026-11-06 | Accepted |
| [0002](0002-langgraph-graph-with-a-critic-loop-and-an-advocate-review-in.md) | LangGraph graph with a critic loop and an advocate-review interrupt | 2026-11-06 | Accepted |
| [0003](0003-law-library-llamaindex-over-pgvector-one-node-per-section-da.md) | Law library: LlamaIndex over pgvector, one node per section, date-filtered hybrid search | 2026-10-29 | Accepted |
| [0004](0004-mcp-for-law-data-only-read-only-no-free-text-to-sql.md) | MCP for law data only, read-only, no free text-to-SQL | 2026-11-01 | Accepted |
| [0005](0005-memory-postgres-checkpoints-one-thread-per-turn.md) | Memory: Postgres checkpoints, one thread per turn | 2026-11-07 | Accepted (supersedes the SQLite checkpointer of 2026-11-06) |
| [0006](0006-rules-first-model-second-basic-mode-and-model-free-safety.md) | Rules first, model second: basic mode and model-free safety | 2026-11-03 | Accepted |
| [0007](0007-azure-openai-with-a-small-and-a-strong-model.md) | Azure OpenAI with a small and a strong model | 2026-10-30 | Accepted |
| [0008](0008-self-hosted-langfuse-for-tracing-scores-and-cost.md) | Self-hosted Langfuse for tracing, scores and cost | 2026-10-29 | Accepted |
| [0009](0009-versioned-prompt-registry.md) | Versioned prompt registry | 2026-11-07 | Accepted |
| [0010](0010-one-uv-project-one-package-laid-out-by-layer.md) | One uv project, one package, laid out by layer | 2026-10-30 | Accepted (supersedes the two-package workspace) |
| [0011](0011-razorpay-test-mode-with-manual-advocate-payouts.md) | Razorpay test mode with manual advocate payouts | 2026-07-18 | Accepted |
