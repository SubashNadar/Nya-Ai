"""Ingestion and hybrid retrieval against a real Postgres with pgvector.

Uses `NYA_TEST_DATABASE_URL` (default: the docker-compose database, `nya_test` schema-free DB)
and a mock embedding, so no Azure key is needed. Skipped when Postgres is not reachable.
"""

import os
from datetime import date
from pathlib import Path

import pytest
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.schema import Document
from sqlalchemy import text

from app.evals.golden import check
from app.rag import index, tables
from app.rag.ingest import ingest_act
from app.rag.retrieve import LawLibrary

URL = os.environ.get("NYA_TEST_DATABASE_URL", "postgresql+psycopg://nya:nya@localhost:5433/nya_test")
FIXTURE = (Path(__file__).parent / "fixtures" / "sample_act.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def lib():
    engine = tables.get_engine(URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception:
        pytest.skip("Postgres with pgvector is not running (docker compose up -d db)")
    with engine.begin() as conn:
        for t in [
            "data_law_sections",
            "data_law_docstore",
            "sections",
            "section_map",
            "offence_class",
            "ingestion_jobs",
            "acts",
        ]:
            conn.execute(text(f"drop table if exists {t} cascade"))
    tables.setup(engine)
    embed = MockEmbedding(embed_dim=1536)
    vs, ds = index.vector_store(URL), index.docstore(URL)
    pages = [Document(text=FIXTURE, metadata={"page_label": "1"})]
    stats = {
        code: ingest_act(code, engine, embed, pages=pages, source_url="test", vector_store=vs, docstore=ds)
        for code in ["BNS", "IPC"]
    }
    return engine, embed, vs, ds, stats, LawLibrary(engine, embed, vector_store=vs)


def test_ingest_records_sections_and_job(lib):
    engine, *_, stats, _ = lib
    assert stats["BNS"]["sections"] == 5
    assert tables.get_section(engine, "BNS", "3A")["heading"] == "Snatching of property"
    with engine.connect() as conn:
        job = (
            conn.execute(tables.ingestion_jobs.select().order_by(tables.ingestion_jobs.c.id.desc())).mappings().first()
        )
    assert job["status"] == "ok" and job["stage"] == "done"
    assert "split" in job["log"] and job["stats"]["sections"] == 5


def test_reingest_unchanged_act_embeds_nothing(lib):
    engine, embed, vs, ds, _, _ = lib
    again = ingest_act(
        "BNS",
        engine,
        embed,
        pages=[Document(text=FIXTURE, metadata={"page_label": "1"})],
        source_url="test",
        vector_store=vs,
        docstore=ds,
    )
    assert again["embedded"] == 0


def test_date_filter_never_mixes_codes(lib):
    *_, library = lib
    before = library.search("snatching of property", as_of=date(2024, 3, 12), acts=["IPC", "BNS"])
    after = library.search("snatching of property", as_of=date(2024, 8, 1), acts=["IPC", "BNS"])
    assert before and {e.act for e in before} == {"IPC"}
    assert after and {e.act for e in after} == {"BNS"}


def test_full_text_finds_the_matching_section(lib):
    *_, library = lib
    hits = library.search("suddenly seizes snatching", as_of=date(2024, 8, 1), acts=["BNS"])
    assert ("BNS", "3A") in [(e.act, e.section) for e in hits[:2]]


def test_exact_section_reference_comes_first(lib):
    *_, library = lib
    hits = library.search("What does BNS section 4 say?", as_of=date(2025, 1, 1))
    assert (hits[0].act, hits[0].section, hits[0].found_by) == ("BNS", "4", "exact")


def test_named_act_not_in_force_is_not_returned_as_exact(lib):
    *_, library = lib
    hits = library.search("IPC 4 punishment", as_of=date(2025, 1, 1))
    assert all(e.act != "IPC" for e in hits)


def test_golden_check(lib, tmp_path):
    engine, *_ = lib
    md = tmp_path / "g.md"
    md.write_text(
        "| 1 | q | Low | rag | none | BNS §3A |\n| 2 | q | Low | rag | none | BNS §999 |\n"
        "| 3 | q | Low | rag | none | BSA §63 |\n| 4 | q | Low | rag | none | RTI Act §7 |\n",
        encoding="utf-8",
    )
    r = check(engine, md)
    assert [(x.act, x.section) for x in r.found] == [("BNS", "3A")]
    assert [(x.act, x.section) for x in r.missing] == [("BNS", "999")]
    assert [x.act for x in r.not_ingested] == ["BSA"]
    assert [x.act for x in r.outside_library] == ["RTI Act"]
    assert not r.ok


def test_ingesting_one_act_leaves_the_other_alone(lib):
    *_, library = lib
    # IPC was ingested after BNS in the fixture, and BNS again in the re-ingest test.
    assert library.search("snatching", as_of=date(2024, 3, 12), acts=["IPC"])
    assert library.search("snatching", as_of=date(2024, 8, 1), acts=["BNS"])


def test_changed_act_replaces_its_old_vectors(lib):
    engine, embed, vs, ds, _, _ = lib
    changed = FIXTURE.replace(
        "3A. Snatching of property.—Taking is snatching if the offender suddenly or quickly seizes the property.\n", ""
    )
    ingest_act(
        "BSA",
        engine,
        embed,
        pages=[Document(text=FIXTURE, metadata={"page_label": "1"})],
        source_url="t",
        vector_store=vs,
        docstore=ds,
    )
    ingest_act(
        "BSA",
        engine,
        embed,
        pages=[Document(text=changed, metadata={"page_label": "1"})],
        source_url="t",
        vector_store=vs,
        docstore=ds,
    )
    with engine.connect() as conn:
        n = conn.execute(text("select count(*) from data_law_sections where metadata_->>'act' = 'BSA'")).scalar_one()
    assert n == 4
    assert tables.get_section(engine, "BSA", "3A") is None
