"""`uv run nya-agent <command>`: fetch, count, setup, ingest, golden, search, status."""

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
    args = p.parse_args()

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
            print(f"{r['act']:<5} {'OK  ' if good else 'DIFF'} {r['numbered']}/{r['expected']} numbered, "
                  f"{r['sections']} total, {r['pages']} pages")
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
            jobs = conn.execute(select(tables.ingestion_jobs).order_by(tables.ingestion_jobs.c.id.desc()).limit(5)).mappings()
            for j in jobs:
                print(f"job {j['id']} {j['act']} {j['stage']} {j['status']} {j['stats']}")
