# ADR 0006: Rules first, model second: basic mode and model-free safety

- **Date:** 2026-11-03
- **Status:** Accepted

## Context

An emergency ("my husband is threatening to kill me") must get helpline numbers even when Azure
or the library is down. A model outage must not take chat down.

## Decision

Input guardrails, PII redaction, emergency detection and refusals are rules (`guards.py`,
`triage.py`); the Azure nano classifier is OR-ed in, so it can only raise the risk. When the library
is unreachable or `AGENT_ENABLED=false`, ordinary questions get the keyword rule engine ("basic
mode", `meta.mode = "basic"`). Without Azure, the writer builds an extractive answer from the
retrieved sections.

## Consequences

Safety never depends on a model being up. Rules generalise worse than the model (safety and
routing 65% to 73% on unseen questions), which is why the model is OR-ed in.

## References

`backend/app/agents/guards.py`, `triage.py`, `safety_llm.py`, `app/services/chat_engine.py`; docs/SLOS.md
