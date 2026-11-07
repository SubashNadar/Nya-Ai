# ADR 0007: Azure OpenAI with a small and a strong model

- **Date:** 2026-10-30
- **Status:** Accepted

## Context

Cost and latency per answer matter for a free legal-information service; quality matters most for
the written answer and the judge.

## Decision

Azure OpenAI on the owner's subscription: gpt-5.4-nano for triage, routing, SQL picking and the
writer's first draft; gpt-5.4 for the critic's retry, SQL-pick retries and the LLM judge;
text-embedding-3-large cut to 1536 dimensions. Deployment names are settings, never hard-coded.

## Consequences

Most calls are cheap and fast; the strong model is used only where it pays. Keys stay in `.env`
and are never committed.

## References

`backend/app/core/config.py`, `app/agents/llm.py`
