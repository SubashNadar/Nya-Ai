"""Ingest one bare act: parse the PDF, split by section, embed, index, record in SQL.

Stages match the law library admin screen: fetch, parse, split, embed, index, eval. Re-running
an unchanged act is cheap: the docstore sees the same text hash and skips embedding.
"""

from pathlib import Path

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.schema import Document, TextNode
from llama_index.readers.file import PDFReader
from sqlalchemy.engine import Engine

from app.core import observability as obs
from app.core.paths import RAW_DIR
from app.rag import tables
from app.rag.acts import ACTS
from app.rag.parser import SectionNodeParser, merge_pages

# Official India Code PDFs (Ministry of Home Affairs uploads for the new codes). See data/SOURCES.md.
SOURCE_URLS = {
    "BNS": "https://indiacode.gov.in/server/api/core/bitstreams/8007a80e-259b-429d-9ca4-1a2f474b5000/content",
    "BNSS": "https://indiacode.gov.in/server/api/core/bitstreams/73f93470-5f6a-4f0f-bc23-1309e32b9554/content",
    "BSA": "https://indiacode.gov.in/server/api/core/bitstreams/fa0f7526-d871-41f2-a644-2a42952211f5/content",
    "IPC": "https://www.indiacode.nic.in/bitstream/123456789/4219/1/THE-INDIAN-PENAL-CODE-1860.pdf",
}
# Numbered sections in each act, for checking the parser on the real PDFs.
EXPECTED_SECTIONS = {"BNS": 358, "BNSS": 531, "BSA": 170, "IPC": 511}


def act_document(code: str, pages: list[Document], source_url: str) -> Document:
    act = ACTS[code]
    doc = merge_pages(
        pages,
        {
            "act": code,
            "act_title": act.title,
            "effective_from": act.effective_from,
            "effective_to": act.effective_to,
            "source_url": source_url,
        },
    )
    doc.id_ = f"act:{code}"
    return doc


def fetch_act(code: str, force: bool = False) -> Path:
    """Download the official PDF for `code` into data/raw/ unless it is already there."""
    import urllib.request

    dest = RAW_DIR / ACTS[code].file
    if dest.exists() and not force:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(SOURCE_URLS[code], headers={"User-Agent": "Mozilla/5.0 (nya-agent)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
    if not body.startswith(b"%PDF"):
        raise ValueError(f"{SOURCE_URLS[code]} did not return a PDF")
    dest.write_bytes(body)
    return dest


def count_sections(code: str, pdf: Path | None = None) -> dict:
    """Parse a PDF without embedding or a database and compare its sections with the expected count."""
    pdf = pdf or RAW_DIR / ACTS[code].file
    pages = PDFReader().load_data(pdf)
    nodes = SectionNodeParser().split_act(act_document(code, pages, SOURCE_URLS.get(code, "")))
    found = {n.metadata["section"] for n in nodes}
    numbered = {int("".join(c for c in s if c.isdigit())) for s in found}
    expected = EXPECTED_SECTIONS[code]
    return {
        "act": code, "pages": len(pages), "sections": len(found), "numbered": len(numbered),
        "expected": expected, "missing": sorted(set(range(1, expected + 1)) - numbered),
        "extra": sorted(n for n in numbered if n > expected),
        "lettered": sorted(s for s in found if not s.isdigit()),
    }


def section_rows(nodes: list[TextNode]) -> list[dict]:
    """One `sections` row per section, joining the parts of a long section back together."""
    rows: dict[str, dict] = {}
    for n in nodes:
        m = n.metadata
        row = rows.setdefault(
            m["section"],
            {
                "act": m["act"], "section": m["section"], "heading": m["heading"], "chapter": m["chapter"],
                "chapter_title": m["chapter_title"], "text": "", "page": m["page"],
                "effective_from": m["effective_from"], "effective_to": m["effective_to"],
            },
        )
        row["text"] = (row["text"] + "\n" + n.text).strip()
    return list(rows.values())


def ingest_act(
    code: str,
    engine: Engine,
    embed: BaseEmbedding,
    pdf: Path | None = None,
    pages: list[Document] | None = None,
    source_url: str = "",
    vector_store=None,
    docstore=None,
) -> dict:
    """Ingest `code` from `pdf` (or pre-read `pages`, used by tests). Returns the job stats."""
    from app.rag import index

    with obs.span(f"ingest {code}", metadata={"act": code}) as trace:
        stats = _ingest(code, engine, embed, pdf, pages, source_url, vector_store, docstore, index)
        trace.update(output=stats)
    client = obs.langfuse()
    if client is not None:
        client.flush()
    return stats


def _ingest(code, engine, embed, pdf, pages, source_url, vector_store, docstore, index) -> dict:
    job = tables.Job(engine, code)
    try:
        if pages is None:
            pdf = pdf or RAW_DIR / ACTS[code].file
            if not pdf.exists():
                raise FileNotFoundError(f"{pdf} not found. See backend/data/SOURCES.md for where to get it.")
            job.stage("fetch", f"local {pdf.name}")
            pages = PDFReader().load_data(pdf)
        source_url = source_url or SOURCE_URLS.get(code, "")
        job.stage("parse", f"pages={len(pages)}", pages=len(pages))

        doc = act_document(code, pages, source_url)
        parser = SectionNodeParser()
        nodes = parser.split_act(doc)
        if not nodes:
            raise ValueError("no sections found; the PDF layout may differ from the parser's pattern")
        sections = sorted({n.metadata["section"] for n in nodes}, key=lambda s: (int("".join(c for c in s if c.isdigit())), s))
        job.stage(
            "split", f"sections={len(sections)} nodes={len(nodes)} range={sections[0]}..{sections[-1]}",
            sections=len(sections), nodes=len(nodes),
        )

        pipeline = IngestionPipeline(
            name=f"law-{code}",
            transformations=[parser, embed],
            vector_store=vector_store or index.vector_store(),
            docstore=docstore or index.docstore(),
            # Each act is one document, so UPSERTS replaces only this act. UPSERTS_AND_DELETE would
            # delete every act not in this run.
            docstore_strategy=DocstoreStrategy.UPSERTS,
        )
        written = pipeline.run(documents=[doc])
        job.stage("embed", f"embedded={len(written)} (0 means unchanged since last run)", embedded=len(written))
        job.stage("index", "pgvector + full-text index updated")

        tables.upsert_sections(engine, code, section_rows(nodes), source_url)
        job.stage("eval", "run `nya-agent golden` to check the golden set against this act")
        job.finish("ok")
        return {"act": code, "sections": len(sections), "nodes": len(nodes), "embedded": len(written)}
    except Exception as e:
        job.stage(job.lines[-1].split()[1] if job.lines else "fetch", f"FAILED {e}")
        job.finish("failed")
        raise
