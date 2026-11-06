"""Consult planner: a draft of the Plan screen from the chat. The rules live in app.services.planner."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas.plan import PlanDraftIn, PlanDraftOut
from app.core.security import get_current_user_optional
from app.db.models import User
from app.db.session import get_db
from app.services import planner as svc

router = APIRouter(prefix="/plan", tags=["plan"])


@router.post("/draft", response_model=PlanDraftOut)
def draft_plan(
    payload: PlanDraftIn, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)
) -> PlanDraftOut:
    return svc.draft(db, payload, user)
