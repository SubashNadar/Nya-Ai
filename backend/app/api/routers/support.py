"""Public Contact page endpoint. No login needed, so a signed-out visitor can reach the team."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas.support import SupportIn, SupportOut
from app.db.models import SupportMessage
from app.db.session import get_db

router = APIRouter(prefix="/support", tags=["support"])


def _next_ref(db: Session) -> str:
    """`SUP-YYYYMMDD-###`, counted per UTC day like booking refs."""
    today = datetime.now(timezone.utc).date()
    prefix = f"SUP-{today:%Y%m%d}-"
    count_today = (
        db.query(func.count(SupportMessage.id)).filter(SupportMessage.ref.like(f"{prefix}%")).scalar() or 0
    )
    return f"{prefix}{count_today + 1:03d}"


@router.post("", response_model=SupportOut, status_code=status.HTTP_201_CREATED)
def create_support_message(payload: SupportIn, db: Session = Depends(get_db)) -> SupportOut:
    message = SupportMessage(
        ref=_next_ref(db),
        name=payload.name.strip(),
        contact=payload.contact.strip(),
        topic=payload.topic,
        text=payload.text.strip(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return SupportOut(ref=message.ref, created_at=message.created_at)
