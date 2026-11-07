# ADR 0008: Self-hosted Langfuse for tracing, scores and cost

- **Date:** 2026-10-29
- **Status:** Accepted

## Context

Every answer must be traceable (which sections, which prompt, which model, how long, how much),
and the course asks for observability and cost tracking. User data must not leave the machine.

## Decision

Langfuse v3, self-hosted in `backend/docker-compose.yml`. Every graph run, ingestion and Azure
call is traced; generations carry token usage, cost (from the `PRICE_*` settings) and the prompt name
and version. PII is masked on export and the user id is hashed. Tracing is off without keys (tests).

## Consequences

Full traces with no third-party data sharing. Prices must be kept current by hand in `.env`
(`nya-agent cost --register-prices`).

## References

`backend/app/core/observability.py`, `app/core/costs.py`, `app/evals/cost.py`
