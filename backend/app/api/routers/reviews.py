"""Advocate review queue (lawyer portal): answers held by the agent until an advocate decides."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas.reviews import ReviewDecisionIn, ReviewOut, ReviewsListOut
from app.core.security import require_lawyer
from app.db.models import User
from app.db.session import get_db
from app.services import agent as svc

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=ReviewsListOut)
def list_reviews(
    status: str | None = Query(default="pending", pattern="^(pending|approved|edited|rejected)$"),
    db: Session = Depends(get_db),
    _: User = Depends(require_lawyer),
) -> ReviewsListOut:
    return ReviewsListOut(reviews=[ReviewOut(**r) for r in svc.list_reviews(db, status)])


@router.get("/{review_id}", response_model=ReviewOut)
def get_review(review_id: str, db: Session = Depends(get_db), _: User = Depends(require_lawyer)) -> ReviewOut:
    return ReviewOut(**svc.review_out(svc.get_review(db, review_id)))


@router.post("/{review_id}", response_model=ReviewOut)
def decide(
    review_id: str, payload: ReviewDecisionIn, db: Session = Depends(get_db), lawyer: User = Depends(require_lawyer)
) -> ReviewOut:
    """Approve, edit or reject; resumes the paused graph run and posts the result into the chat."""
    return ReviewOut(**svc.decide(db, svc.get_review(db, review_id), lawyer, payload.model_dump()))
