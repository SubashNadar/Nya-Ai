"""Dashboard endpoints (per-role summary stats). The rules live in app.services.dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas.dashboard import LawyerDashboardOut, UserDashboardOut
from app.core.security import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.services import dashboard as svc

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/user", response_model=UserDashboardOut)
def user_dashboard(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> UserDashboardOut:
    return svc.user_summary(db, user)


@router.get("/lawyer", response_model=LawyerDashboardOut)
def lawyer_dashboard(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> LawyerDashboardOut:
    return svc.lawyer_summary(db, user)
