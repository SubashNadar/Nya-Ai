# ADR 0009: Versioned prompt registry

- **Date:** 2026-11-07
- **Status:** Accepted

## Context

Prompts were inline constants in five modules. A silent prompt edit can change answers without
anyone noticing, and Langfuse could not tell which prompt version produced a trace.

## Decision

All prompts are `Prompt` records in `app/agents/prompts/` with a name, semver version, pattern,
purpose and model. A test pins each version and text hash. Generations are tagged with the prompt's
name, version and hash.

## Consequences

Every prompt change is a deliberate, reviewed version bump, comparable across versions in
Langfuse. Slightly more ceremony for small wording changes.

## References

`docs/PROMPTS.md`, `backend/app/agents/prompts/`
