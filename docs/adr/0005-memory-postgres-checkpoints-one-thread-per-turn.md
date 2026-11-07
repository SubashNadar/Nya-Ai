# ADR 0005: Memory: Postgres checkpoints, one thread per turn

- **Date:** 2026-11-07
- **Status:** Accepted (supersedes the SQLite checkpointer of 2026-11-06)

## Context

Answers held for advocate review must survive a restart. The graph state is built for one
question (one evidence set, one draft). The conversation must be visible to the user and deletable.

## Decision

LangGraph checkpoints in Postgres (`CHECKPOINT_DATABASE_URL`, the local `nya-ai` database), with
SQLite as the fallback. Each turn runs on its own thread id; conversation context comes from
`chat_messages` (the last 4 turns, PII-redacted).

## Consequences

Held reviews survive restarts and turns cannot contaminate each other. There are two stores to
govern (checkpoints and chat rows); retention is proposed but not automated yet.

## References

`docs/MEMORY.md`, `backend/app/agents/runner.py`
