"""Law library admin (advocate accounts): acts, section counts, ingestion jobs, start ingestion."""

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.schemas.library import IngestIn, IngestOut, LibraryOut
from app.core.security import require_lawyer
from app.db.models import User
from app.services import library as svc

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/acts", response_model=LibraryOut)
def acts(_: User = Depends(require_lawyer)) -> LibraryOut:
    return svc.overview()


@router.post("/ingest", response_model=IngestOut, status_code=status.HTTP_202_ACCEPTED)
def ingest(payload: IngestIn, background: BackgroundTasks, _: User = Depends(require_lawyer)) -> IngestOut:
    """Checks the PDFs, Azure and the database first; the run itself continues in the background."""
    out = svc.start(payload.acts)
    background.add_task(svc.run_ingest, out.started)
    return out
