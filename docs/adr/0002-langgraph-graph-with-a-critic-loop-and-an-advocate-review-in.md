# ADR 0002: LangGraph graph with a critic loop and an advocate-review interrupt

- **Date:** 2026-11-06
- **Status:** Accepted

## Context

Answers must cite real sections and never give advice on the user's own case, and a live matter
(arrest, custody, court date) must be checked by an advocate before the user sees it. A single prompt
cannot guarantee any of this.

## Decision

A LangGraph state graph: guard (input guardrails and triage), temporal (which acts apply on the
incident date), router, statute researcher and SQL agent in parallel for hybrid questions, writer,
critic (code checks citations against the evidence and looks for advice, and sends the draft back to
the writer once), advocate review with `interrupt()` for live matters, answer.

## Consequences

Safety and grounding are enforced in code, not left to the model. A held answer waits in the
checkpointer until an advocate decides in `/api/reviews`. More moving parts than a single chain; every
node is traced in Langfuse to keep it debuggable.

## References

`backend/app/agents/graph.py`, `runner.py`; tests in `tests/agents/test_graph.py`
