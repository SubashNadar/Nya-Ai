# ADR 0010: One uv project, one package, laid out by layer

- **Date:** 2026-10-30
- **Status:** Accepted (supersedes the two-package workspace)

## Context

The API and the agent started as separate packages with separate settings, which duplicated
configuration and made imports between them awkward.

## Decision

All Python is one uv project in `backend/` with one package, `app`: `api/`, `core/`, `db/`,
`services/`, `agents/`, `rag/` and `evals/`. One `.env`; the law library's URL is
`VECTOR_DATABASE_URL`. Routers are HTTP only; business rules live in `services/` and raise service
errors that `main.py` maps to HTTP responses.

## Consequences

One lockfile and one virtualenv; Ruff, pylint and pytest run over everything at once.

## References

`backend/README.md`, `backend/pyproject.toml`
