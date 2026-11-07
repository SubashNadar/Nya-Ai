# ADR 0003: Law library: LlamaIndex over pgvector, one node per section, date-filtered hybrid search

- **Date:** 2026-10-29
- **Status:** Accepted

## Context

Users ask about incidents before and after 1 July 2024, when the BNS, BNSS and BSA replaced the
IPC, CrPC and Evidence Act. Answers must cite the act in force on the incident date, by exact section.

## Decision

Bare-act PDFs from India Code are parsed into one node per section (explanations and illustrations
kept with it, long sections split at sub-sections, schedules left out). Azure text-embedding-3-large at
1536 dimensions goes into pgvector through a LlamaIndex `IngestionPipeline`, with a full-text column.
Retrieval filters to the acts in force on the date (ISO strings, `9999-12-31` means in force), then
fuses vector and full-text results by reciprocal rank. Section numbers in the question are looked up
directly. One document per act with `UPSERTS`, so re-ingesting one act never touches another.

## Consequences

Citations are exact and date-correct; the golden check finds all 23 sections in scope. Ranking
still needs tuning (theft ranks 3rd to 5th for "my phone was stolen"). A parser change bumps
`PARSER_VERSION`, so stored acts are re-embedded.

## References

`backend/app/rag/`; CLAUDE.md log of 2026-11-07
