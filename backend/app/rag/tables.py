"""SQL tables beside the vector index, in the same Postgres.

`sections` is the exact-lookup and citation-check table: the critic checks every cited section
against it. `section_map` and `offence_class` feed the SQL agent in R2. `ingestion_jobs` records
each ingestion run stage by stage, which the law library admin screen reads.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine

from app.core import observability as obs
from app.core.config import get_settings
from app.rag.acts import ACTS

metadata = MetaData()

acts = Table(
    "acts",
    metadata,
    Column("code", String(12), primary_key=True),
    Column("title", Text, nullable=False),
    Column("in_force_from", Date, nullable=False),
    Column("repealed_on", Date),
    Column("replaced_by", String(12)),
    Column("source_url", Text),
    Column("sections", Integer, nullable=False, default=0),
    Column("ingested_at", DateTime(timezone=True)),
)

sections = Table(
    "sections",
    metadata,
    Column("act", String(12), primary_key=True),
    Column("section", String(8), primary_key=True),
    Column("heading", Text, nullable=False),
    Column("chapter", String(12)),
    Column("chapter_title", Text),
    Column("text", Text, nullable=False),
    Column("page", String(12)),
    Column("effective_from", String(10), nullable=False),
    Column("effective_to", String(10), nullable=False),
)

section_map = Table(
    "section_map",
    metadata,
    Column("old_act", String(12), primary_key=True),
    Column("old_section", String(16), primary_key=True),
    Column("new_act", String(12), primary_key=True),
    Column("new_section", String(16), primary_key=True),  # "" when there is no equivalent
    Column("note", Text),
    # True only once the row has been checked against the official MHA comparison table.
    Column("verified", Boolean, nullable=False, default=False),
)

offence_class = Table(
    "offence_class",
    metadata,
    Column("act", String(12), primary_key=True),
    Column("section", String(16), primary_key=True),
    Column("offence", Text, nullable=False),
    Column("punishment", Text),
    Column("cognizable", Boolean),
    Column("bailable", Boolean),
    Column("triable_by", Text),
    Column("life_or_death", Boolean),
)

ingestion_jobs = Table(
    "ingestion_jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("act", String(12), nullable=False),
    Column("stage", String(16), nullable=False),  # fetch parse split embed index eval done
    Column("status", String(12), nullable=False),  # running ok failed
    Column("stats", JSONB, nullable=False, default=dict),
    Column("log", Text, nullable=False, default=""),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True)),
)


def get_engine(url: str | None = None) -> Engine:
    return create_engine(url or get_settings().VECTOR_DATABASE_URL)


def setup(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    metadata.create_all(engine)
    with engine.begin() as conn:
        for a in ACTS.values():
            stmt = insert(acts).values(
                code=a.code, title=a.title, in_force_from=a.in_force_from, repealed_on=a.repealed_on,
                replaced_by=a.replaced_by, sections=0,
            )
            conn.execute(stmt.on_conflict_do_update(
                index_elements=["code"],
                set_={"title": a.title, "in_force_from": a.in_force_from, "repealed_on": a.repealed_on,
                      "replaced_by": a.replaced_by},
            ))


def upsert_sections(engine: Engine, act: str, rows: list[dict], source_url: str) -> None:
    """Replace one act's rows in `sections` and record the count and time on `acts`."""
    with engine.begin() as conn:
        conn.execute(sections.delete().where(sections.c.act == act))
        if rows:
            conn.execute(sections.insert(), rows)
        conn.execute(
            acts.update().where(acts.c.code == act).values(
                sections=len(rows), source_url=source_url, ingested_at=datetime.now(timezone.utc)
            )
        )


def get_section(engine: Engine, act: str, section: str) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            select(sections).where(sections.c.act == act, sections.c.section == section)
        ).mappings().first()
    return dict(row) if row else None


def existing_sections(engine: Engine) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    with engine.connect() as conn:
        for act, sec in conn.execute(select(sections.c.act, sections.c.section)):
            out.setdefault(act, set()).add(sec)
    return out


def load_section_map(engine: Engine, path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        rows = [
            {**r, "verified": r.get("verified", "").strip().lower() == "true"}
            for r in csv.DictReader(f)
            if not r["old_act"].startswith("#")
        ]
    with engine.begin() as conn:
        for r in rows:
            stmt = insert(section_map).values(**r)
            conn.execute(stmt.on_conflict_do_update(
                index_elements=["old_act", "old_section", "new_act", "new_section"],
                set_={"note": r["note"], "verified": r["verified"]},
            ))
    return len(rows)


class Job:
    """One ingestion run. Each stage change is written straight away so a viewer sees progress."""

    def __init__(self, engine: Engine, act: str):
        self.engine, self.act, self.lines = engine, act, []
        with engine.begin() as conn:
            self.id = conn.execute(
                ingestion_jobs.insert().values(
                    act=act, stage="fetch", status="running", stats={}, log="",
                    started_at=datetime.now(timezone.utc),
                ).returning(ingestion_jobs.c.id)
            ).scalar_one()

    def stage(self, stage: str, message: str, **stats) -> None:
        stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.lines.append(f"{stamp} {stage:<6} {message}")
        print(self.lines[-1])
        with obs.span(f"ingest.{stage}", input=message, metadata={"act": self.act, "job_id": self.id, **stats}):
            pass
        with self.engine.begin() as conn:
            row = conn.execute(select(ingestion_jobs.c.stats).where(ingestion_jobs.c.id == self.id)).scalar_one()
            conn.execute(ingestion_jobs.update().where(ingestion_jobs.c.id == self.id).values(
                stage=stage, stats={**row, **stats}, log="\n".join(self.lines),
            ))

    def finish(self, status: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(ingestion_jobs.update().where(ingestion_jobs.c.id == self.id).values(
                status=status, stage="done" if status == "ok" else self.lines[-1].split()[1] if self.lines else "fetch",
                finished_at=datetime.now(timezone.utc),
            ))
