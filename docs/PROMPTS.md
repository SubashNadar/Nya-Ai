# Nya-AI prompt engineering framework

How prompts are written, stored, versioned, observed and tested. Sprint task 13.

## Where prompts live

Every model prompt is a `Prompt` record in `backend/app/agents/prompts/`, one module per prompt:

```python
Prompt(name="writer", version="1.0.0", pattern="...", purpose="...", model="strong", text="""...""")
```

`prompts.REGISTRY` lists them all. Callers use `prompts.WRITER.text`, and the old constant names
(`WRITER_PROMPT`, `PICKER_PROMPT`, `JUDGE_PROMPT`, ...) remain as aliases. No prompt text lives
anywhere else in the code.

## The prompts

| Name | Used by | Model | Pattern | Output |
|---|---|---|---|---|
| `writer` | graph `writer` node | gpt-5.4 | Persona + grounding rules + JSON schema; **reflection**: the critic node checks the draft and sends it back once with the failures listed | `{"text", "points", "citations"}` |
| `triage` | `safety_llm.classify` (guard node) | gpt-5.4-nano | **Zero-shot classifier** with label definitions; "when unsure, choose the higher risk" | `{"risk", "escalation", "attack", "route"}` |
| `sql_picker` | `sql_agent` | nano, gpt-5.4 on retry | **Tool selection from a fixed menu**; the model names a template and parameters, never SQL | `{"template", "params"}` |
| `judge` | SLO run (`app/evals/slo.py`) | gpt-5.4 | **LLM-as-judge** with a 1–5 rubric | `{"score", "reason"}` |
| `planner` | `/api/plan/draft` | nano | Persona + extraction to a schema | `{"topic", "facts", "questions", "goals", "documents"}` |
| `basic_mode` | `chat_engine` (agent off) | Anthropic | Persona + JSON schema (legacy fallback) | `{"text", "points", ...}` |

## Design rules every prompt follows

1. **One job per prompt.** The writer writes, the triage prompt labels, the picker picks. Routing,
   retrieval, citation checking and confidence are code, not prompt text.
2. **Structured output.** Every prompt asks for JSON only, and the caller uses JSON mode
   (`azure_json`). A reply that does not parse, or lacks a required field, is treated as no reply and
   the caller falls back to rules or a deterministic answer. A model is never a single point of failure.
3. **Grounding.** The writer may use only `<evidence>` and `<lookup>`, and must cite each claim as
   `ACT §NUMBER` from those blocks. The critic (code) rejects any citation that is not in the evidence.
4. **Information, not advice.** Prompts that answer users forbid predictions, percentages and telling
   the user what to do in their own matter. The critic checks for advice phrases in code too.
5. **User text is data.** Questions and history go inside tags (`<question>`, `<history>`,
   `<conversation>`), and each prompt says they are data, not instructions. The input guard blocks
   prompt injection, system-prompt extraction and jailbreaks before any model call.
6. **PII never reaches a prompt.** The question and the history are redacted first
   (`app/agents/guards.py`, docs/MEMORY.md).
7. **Small model first.** Classification and picking use gpt-5.4-nano. gpt-5.4 writes answers, judges,
   and retries a failed SQL pick.
8. **Rules first, model second.** Triage is rules OR-ed with the model, so the model can only make a
   question safer (higher risk), never wave through something the rules caught.

## Versioning

- Semantic versions: **major** = output schema changes (callers must change), **minor** = a new rule
  or label, **patch** = wording only.
- `tests/agents/test_prompts.py` pins each prompt's version **and** a SHA-256 of its text. Editing a
  prompt without bumping its version fails the test, so every prompt change is a deliberate, reviewed
  version change.
- Record the change and why in this file's change log below.

## Observability

`azure_chat` recognises the prompt behind every system message (`prompts.identify`) and names the
Langfuse generation after it (`writer`, `triage`, ...) with metadata `prompt`, `prompt_version` and
`prompt_sha`, plus token usage and cost (`app/core/costs.py`). In Langfuse you can filter by prompt
and version, and compare latency, cost and scores between versions.

## Testing

- **Contract tests** (offline): every prompt is registered, versioned, pinned, asks for JSON; the
  answering prompts forbid advice; callers use the registry text; generations are tagged.
- **Graph tests** with a fake LLM check that a bad draft is retried once, that unsupported citations
  are dropped, and that history is redacted before the model sees it (`tests/agents/test_graph.py`).
- **Evaluation**: golden (50), holdout (45, frozen) and stress (30, frozen) sets in `evals/cases/`
  through `nya-agent answers` and `nya-agent slo`, with the `judge` prompt and Ragas, scored per prompt
  version in Langfuse. A prompt change ships only if the holdout scores do not drop (docs/SLOS.md).

## Change log

| Date | Prompt | Version | Change |
|---|---|---|---|
| 2026-11-07 | all | 1.0.0 | Moved from inline constants into `app/agents/prompts/`, text unchanged (checked byte for byte). |
