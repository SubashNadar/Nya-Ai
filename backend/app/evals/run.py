"""`nya-agent slo`: run what can run, print the 16-row matrix, save it, optionally push to Langfuse."""

import argparse
import json
import time
from pathlib import Path

from app.core.paths import EVALS_DIR
from app.evals import slo
from app.evals.rbac import run_probes


def add_parser(sub) -> None:
    p = sub.add_parser("slo", help="validate the 16 SLOs (offline ones always; answer metrics from a run file)")
    p.add_argument("--llm", action="store_true", help="add the Azure safety classifier on top of the rules")
    p.add_argument("--answers", type=Path, help="JSONL of agent answers to score (metrics 1-8, 10)")
    p.add_argument("--ragas", action="store_true", help="score --answers with Ragas (uv sync --group eval)")
    p.add_argument("--judge", action="store_true", help="score --answers with the gpt-5.4 judge")
    p.add_argument("--sql-url", help="Postgres with the law tables (default VECTOR_DATABASE_URL)")
    p.add_argument("--push", action="store_true", help="send the scores to Langfuse")
    p.add_argument("--out", type=Path, default=EVALS_DIR / "slo-results.json")


def _sql(url: str | None) -> dict:
    from sqlalchemy.exc import OperationalError, ProgrammingError

    from app.rag import tables

    try:
        return slo.score_sql(tables.get_engine(url))
    except OperationalError as e:
        return {"sql_correctness": None, "error": f"database not reachable: {e.orig}"}
    except ProgrammingError:
        return {"sql_correctness": None, "error": "law tables missing: run `nya-agent setup` first"}


def _guard_latency_ms(cases: list[dict]) -> float:
    from app.agents.triage import triage

    start = time.perf_counter()
    for _ in range(20):
        for c in cases:
            triage(c["query"])
    return (time.perf_counter() - start) * 1000 / (20 * len(cases))


def main(args: argparse.Namespace) -> None:
    predict = _with_model if args.llm else slo.triage

    details: dict = {"triage": {}}
    for split in slo.SPLITS:
        details["triage"][split] = slo.score_triage(slo.load_cases(split), predict)
    unseen = slo.score_triage(slo.load_cases("holdout") + slo.load_cases("stress"), predict)
    details["triage"]["unseen"] = unseen
    details["guard_latency_ms"] = _guard_latency_ms(slo.load_cases("golden"))
    details["sql"] = _sql(args.sql_url)
    probes = run_probes()
    details["rbac"] = [p.__dict__ for p in probes]

    values: dict = {k: unseen[k] for k in slo.BY_KEY if k in unseen}
    values["sql_correctness"] = details["sql"].get("sql_correctness")
    values["rbac_violations"] = sum(p.violated for p in probes)

    records = []
    if args.answers:
        records = [json.loads(line) for line in args.answers.read_text(encoding="utf-8").splitlines() if line.strip()]
        ragas = slo.ragas_scores(records) if args.ragas else None
        judge = [s for s in (slo.llm_judge(r) for r in records) if s is not None] if args.judge else None
        values.update(slo.score_answers(records, ragas, judge))

    print(slo.render(values))
    print("\nTriage by split (rules" + (" + model" if args.llm else "") + "):")
    for split, t in details["triage"].items():
        print(
            f"  {split:<8} n={t['cases']:<3} critical miss {_pct(t['critical_miss_rate'])}  "
            f"escalation recall {_pct(t['escalation_recall'])}  guardrails {_pct(t['guardrail_effectiveness'])}  "
            f"routing {_pct(t['routing_accuracy'])}  risk {_pct(t['risk_accuracy'])}  "
            f"false refusals {_pct(t['guardrail_false_positive_rate'])}"
        )
    print(f"  guard + triage time per question: {details['guard_latency_ms']:.2f} ms")
    if details["sql"].get("failures"):
        print("SQL failures: " + ", ".join(f["id"] for f in details["sql"]["failures"]))
    if details["sql"].get("error"):
        print("SQL: " + details["sql"]["error"])
    slo.save(values, details, args.out)
    print(f"saved {args.out}")
    if args.push:
        pushed = slo.push_to_langfuse(values, "llm" if args.llm else "rules", records)
        print("pushed to Langfuse" if pushed else "Langfuse not configured; nothing pushed")


def _with_model(question: str):
    from app.agents.safety_llm import classify, combine

    return combine(slo.triage(question), classify(question))


def _pct(v: float | None) -> str:
    return "—" if v is None else f"{v:.0%}"
