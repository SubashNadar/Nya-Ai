"""`nya-agent answers`: run the golden and held-out questions through the R1 graph into a JSONL run.

Each line has the fields `app.evals.slo.score_answers` reads (see its module docstring), so the
answer metrics (faithfulness, relevance, precision, recall, latency, attribution...) can be
scored with `nya-agent slo --answers run.jsonl --ragas --judge --push`.
"""

import json
import time
import uuid
from pathlib import Path

from app.agents.guards import citations
from app.evals.slo import load_cases


def record(case: dict, runner) -> dict:
    start = time.perf_counter()
    result = runner.run(case["query"], uuid.uuid4().hex)
    latency = time.perf_counter() - start
    a = result.answer
    return {
        "id": case["id"],
        "question": case["query"],
        "answer": " ".join([a.text, *a.points]),
        "contexts": [e.text for e in result.evidence],
        "evidence": [[e.act, e.section] for e in result.evidence],
        "expected_sections": sorted(citations(case.get("expected") or "")),
        "latency_s": round(latency, 3),
        "trace_id": result.trace_id,
        "risk": a.risk,
        "route": a.route,
        "escalation": a.escalation,
        "status": a.status,
        "confidence": a.confidence,
    }


def run_answers(splits: list[str], out: Path, runner=None) -> int:
    from app.agents.runner import AgentRunner

    runner = runner or AgentRunner()
    n = 0
    with out.open("w", encoding="utf-8") as f:
        for split in splits:
            for case in load_cases(split):
                f.write(json.dumps(record(case, runner), ensure_ascii=False) + "\n")
                n += 1
    return n
