"""Law library admin: the acts, their section counts and ingestion jobs; start an ingestion run."""

from datetime import datetime

from pydantic import BaseModel, Field


class IngestionJobOut(BaseModel):
    id: int
    act: str
    stage: str  # fetch parse split embed index eval done
    status: str  # running ok failed
    stats: dict
    started_at: datetime
    finished_at: datetime | None


class LibraryActOut(BaseModel):
    code: str
    title: str
    in_force_from: str
    repealed_on: str | None
    replaced_by: str | None
    sections: int  # in the SQL `sections` table; 0 until ingested
    ingested_at: datetime | None
    pdf_present: bool  # backend/data/raw/<file> exists on this machine
    last_job: IngestionJobOut | None


class LibraryOut(BaseModel):
    reachable: bool  # Postgres with the law tables answered
    azure: bool  # embeddings configured, needed to ingest
    acts: list[LibraryActOut]
    jobs: list[IngestionJobOut]


class IngestIn(BaseModel):
    acts: list[str] = Field(default_factory=lambda: ["BNS", "BNSS", "BSA", "IPC"], min_length=1, max_length=4)


class IngestOut(BaseModel):
    started: list[str]
