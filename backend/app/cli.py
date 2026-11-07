"""`uv run nya-agent <command>`: fetch, count, setup, ingest, golden, search, status, ask, answers, slo, cost, mcp."""

import argparse
from datetime import date
from pathlib import Path

from app.core.paths import SECTION_MAP_CSV
from app.rag import tables


def main() -> None:
    p = argparse.ArgumentParser(prog="nya-agent", description="Nya-AI law library (release R0)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="create tables, register the acts and load the IPC to BNS map")
    f = sub.add_parser("fetch", help="download the official India Code PDFs into backend/data/raw/")
    f.add_argument("acts", nargs="*", default=["BNS", "BNSS", "BSA", "IPC"])
    f.add_argument("--force", action="store_true", help="download again even if the file exists")
    cnt = sub.add_parser("count", help="parse the PDFs and check section counts (no database, no Azure)")
    cnt.add_argument("acts", nargs="*", default=["BNS", "BNSS", "BSA", "IPC"])
    ing = sub.add_parser("ingest", help="ingest acts from backend/data/raw/")
    ing.add_argument("acts", nargs="*", default=["BNS", "BNSS", "BSA", "IPC"])
    gold = sub.add_parser("golden", help="check golden-set sections against the ingested text")
    gold.add_argument("path", type=Path, help="path to evals/GOLDEN-QUERIES.md (legal-docs-platform)")
    s = sub.add_parser("search", help="try a question against the library")
    s.add_argument("question")
    s.add_argument("--as-of", type=date.fromisoformat, default=None, help="date the law is needed for")
    sub.add_parser("status", help="acts and the last ingestion jobs")
    ask = sub.add_parser("ask", help="run one question through the R1 agent graph and print its trace")
    ask.add_argument("question")
    ans = sub.add_parser(
        "answers", help="run the golden and held-out questions through the graph (for `slo --answers`)"
    )
    ans.add_argument("--splits", nargs="*", default=["golden", "holdout"])
    ans.add_argument("--out", type=Path, default=Path("run.jsonl"))
    cost = sub.add_parser("cost", help="token use and cost per day and per trace, from Langfuse")
    cost.add_argument("--days", type=int, default=14)
    cost.add_argument("--traces", type=int, default=10, help="how many recent traces to list")
    cost.add_argument("--register-prices", action="store_true", help="write the PRICE_* settings into Langfuse")
    m = sub.add_parser("mcp", help="run the read-only law tools as an MCP server (stdio, or --http)")
    m.add_argument("--http", action="store_true", help="streamable HTTP instead of stdio")
    m.add_argument("--host", default="127.0.0.1")
    m.add_argument("--port", type=int, default=8765)
    from app.evals import run as slo_run

    slo_run.add_parser(sub)
    args = p.parse_args()

    if args.cmd == "mcp":
        from app.agents.mcp_server import main as mcp_main

        mcp_main(http=args.http, host=args.host, port=args.port)
        return
    if args.cmd == "cost":
        from app.evals import cost as cost_report

        if args.register_prices:
            for line in cost_report.register_prices():
                print("registered", line)
        print(cost_report.render(cost_report.daily(args.days), cost_report.per_trace(), args.traces))
        return
    if args.cmd == "slo":
        slo_run.main(args)
        return

    if args.cmd == "ask":
        import uuid

        from app.agents.runner import AgentRunner

        r = AgentRunner().run(args.question, uuid.uuid4().hex)
        for line in r.answer.trace:
            print(f"  {line}")
        print(f"\n[{r.answer.status}] {r.answer.text}")
        for point in r.answer.points:
            print(f"  - {point}")
        print(r.answer.citation_line)
        return
    if args.cmd == "answers":
        from app.evals.answers import run_answers

        n = run_answers(args.splits, args.out)
        print(f"{n} answers written to {args.out}; score them with `nya-agent slo --answers {args.out}`")
        return

    if args.cmd == "fetch":
        from app.rag.ingest import fetch_act

        for code in args.acts:
            path = fetch_act(code.upper(), args.force)
            print(f"{code.upper():<5} {path} ({path.stat().st_size // 1024} KB)")
        return
    if args.cmd == "count":
        from app.rag.ingest import count_sections

        ok = True
        for code in args.acts:
            r = count_sections(code.upper())
            good = not r["missing"] and not r["extra"]
            ok &= good
            print(
                f"{r['act']:<5} {'OK  ' if good else 'DIFF'} {r['numbered']}/{r['expected']} numbered, "
                f"{r['sections']} total, {r['pages']} pages"
            )
            if r["missing"]:
                print(f"      missing: {r['missing'][:40]}{' ...' if len(r['missing']) > 40 else ''}")
            if r["extra"]:
                print(f"      beyond the last section: {r['extra'][:20]}")
            if r["lettered"]:
                print(f"      lettered: {len(r['lettered'])} e.g. {r['lettered'][:8]}")
        raise SystemExit(0 if ok else 1)

    engine = tables.get_engine()
    if args.cmd == "setup":
        tables.setup(engine)
        n = tables.load_section_map(engine, SECTION_MAP_CSV)
        print(f"tables ready; {n} section_map rows loaded")
    elif args.cmd == "ingest":
        from app.rag import index
        from app.rag.ingest import ingest_act

        tables.setup(engine)
        embed = index.embed_model()
        for code in args.acts:
            print(ingest_act(code.upper(), engine, embed))
    elif args.cmd == "golden":
        from app.evals.golden import check, render

        report = check(engine, args.path)
        print(render(report))
        raise SystemExit(0 if report.ok else 1)
    elif args.cmd == "search":
        from app.rag import index
        from app.rag.retrieve import LawLibrary

        for e in LawLibrary(engine, index.embed_model()).search(args.question, args.as_of):
            print(f"[{e.found_by} {e.score:.3f}] {e.act} §{e.section} {e.heading} (p. {e.page})")
    elif args.cmd == "status":
        from sqlalchemy import select

        with engine.connect() as conn:
            for a in conn.execute(select(tables.acts)).mappings():
                print(f"{a['code']:<5} {a['sections']:>4} sections  ingested {a['ingested_at'] or 'never'}")
            jobs = conn.execute(
                select(tables.ingestion_jobs).order_by(tables.ingestion_jobs.c.id.desc()).limit(5)
            ).mappings()
            for j in jobs:
                print(f"job {j['id']} {j['act']} {j['stage']} {j['status']} {j['stats']}")
