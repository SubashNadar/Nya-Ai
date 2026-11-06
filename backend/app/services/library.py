"""Law library admin: what is ingested, the ingestion jobs, and starting an ingestion run.

Reads the law tables in Postgres (`VECTOR_DATABASE_URL`). Ingestion needs the PDFs in
`backend/data/raw/` and the Azure embedding key, so it checks both before it starts, then runs
in the background; the jobs list shows each stage as `app.rag.tables.Job` writes it.
"""

import logging
from datetime import date

from sqlalchemy import inspect, select

from app.agents.llm import azure_configured
from app.api.schemas.library import IngestionJobOut, IngestOut, LibraryActOut, LibraryOut, SearchHit, SearchOut
from app.core.paths import RAW_DIR
from app.rag.acts import ACTS
from app.services.errors import Invalid, Unavailable

logger = logging.getLogger(__name__)


class _Empty(Exception):
    """The database answered but the law tables do not exist yet."""


def _engine():
    from app.agents.graph import law_engine

    return law_engine()


def _job(row) -> IngestionJobOut:
    return IngestionJobOut(**{k: row[k] for k in list(IngestionJobOut.model_fields)} | {"stats": row["stats"] or {}})


def overview() -> LibraryOut:
    from app.rag import tables

    stored: dict = {}
    jobs: list = []
    reachable = True
    try:
        with _engine().connect() as conn:
            if not inspect(conn).has_table("acts"):
                raise _Empty  # reachable, nothing ingested yet
            stored = {r["code"]: r for r in conn.execute(select(tables.acts)).mappings()}
            jobs = list(
                conn.execute(
                    select(tables.ingestion_jobs).order_by(tables.ingestion_jobs.c.id.desc()).limit(20)
                ).mappings()
            )
    except _Empty:
        pass
    except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught  # show the acts anyway
        logger.warning("law library not reachable: %s", e)
        reachable = False
    acts = []
    for code, act in ACTS.items():
        row = stored.get(code) or {}
        last = next((j for j in jobs if j["act"] == code), None)
        acts.append(
            LibraryActOut(
                code=code,
                title=act.title,
                in_force_from=act.effective_from,
                repealed_on=act.repealed_on.isoformat() if act.repealed_on else None,
                replaced_by=act.replaced_by,
                sections=int(row.get("sections") or 0),
                ingested_at=row.get("ingested_at"),
                pdf_present=(RAW_DIR / act.file).exists(),
                last_job=_job(last) if last else None,
            )
        )
    return LibraryOut(reachable=reachable, azure=azure_configured(), acts=acts, jobs=[_job(j) for j in jobs])


def check_ingest(codes: list[str]) -> list[str]:
    codes = [c.upper() for c in codes]
    unknown = [c for c in codes if c not in ACTS]
    if unknown:
        raise Invalid(f"Unknown acts: {', '.join(unknown)}")
    if not azure_configured():
        raise Unavailable("Azure OpenAI is not configured: set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
    missing = [ACTS[c].file for c in codes if not (RAW_DIR / ACTS[c].file).exists()]
    if missing:
        raise Invalid(f"PDFs missing from backend/data/raw/: {', '.join(missing)} (run `nya-agent fetch`)")
    try:
        with _engine().connect():
            pass
    except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        raise Unavailable("The law library database is not reachable: start `docker compose up -d`") from e
    return codes


def run_ingest(codes: list[str]) -> None:
    """Background task: one ingestion run per act, in order."""
    from app.rag import index, tables
    from app.rag.ingest import ingest_act

    engine = _engine()
    tables.setup(engine)
    embed = index.embed_model()
    for code in codes:
        try:
            ingest_act(code, engine, embed)
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught  # the job row records it
            logger.exception("ingestion of %s failed", code)


def start(codes: list[str]) -> IngestOut:
    return IngestOut(started=check_ingest(codes))


def search(query: str, as_of: date | None, acts: list[str]) -> SearchOut:
    """The same retrieval the agent's statute researcher uses (LlamaIndex hybrid when embeddings are set)."""
    from app.agents.graph import library_search
    from app.rag.acts import acts_in_force

    day = as_of or date.today()
    codes = [c.upper() for c in acts if c.upper() in ACTS] or list(ACTS)
    scope = acts_in_force(day, codes) or codes
    evidence, ok = library_search(query, day, codes)
    hits = [
        SearchHit(
            act=e.act,
            section=e.section,
            heading=e.heading,
            text=e.text[:900],
            page=e.page,
            score=round(e.score, 4),
            found_by=e.found_by,
        )
        for e in evidence
    ]
    return SearchOut(
        mode="hybrid" if azure_configured() else "exact",
        library_ok=ok,
        as_of=day,
        acts_in_scope=scope,
        hits=hits,
    )
