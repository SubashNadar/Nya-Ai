"""LangGraph agents (release R1).

- `guards`, `triage`, `safety_llm`: input and output guardrails, rule triage and the Azure safety layer.
- `graph`: the R1 graph (guard, temporal, router, statute researcher, SQL agent, writer, critic,
  advocate review with `interrupt()`), built over injectable `Tools`.
- `sql_agent`: picks a parameterized template from `app.rag.sql_queries`.
- `runner`: checkpointing, Langfuse tracing and scores, streaming and resume.

`app.services.agent` calls the runner for chat and `/v1`; `app.services.chat_engine` is the
basic-mode fallback. Retrieval comes from `app.rag`.
"""
