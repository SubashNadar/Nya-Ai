# ADR 0001: One FastAPI service with the agent in process

- **Date:** 2026-11-06
- **Status:** Accepted

## Context

Nya-AI needs a product API (auth, chat, bookings, payments, advocate portal) and an agent (LangGraph
over a law library). The capstone is run and demonstrated by one person on one machine, and the
grading rubric asks for a FastAPI service.

## Decision

The R1 graph runs inside the same FastAPI app (`backend/app`). Chat calls it in process through
`app/services/agent.py`. The agent is also exposed on its own at `/v1/answer`, `/v1/answer/stream`
(SSE, one event per graph node), `/v1/review` and `/v1/health`, next to `/api/*`.

## Consequences

One process to run, debug and deploy, and no network hop on every turn. The `/v1` routes keep a
clean boundary, so the agent can be split into its own service later without changing clients. The
agent cannot be scaled separately until then.

## References

DECISIONS.md "R1 agent graph and APIs"; `backend/app/main.py`, `app/api/routers/agent.py`
