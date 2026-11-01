"""Payment endpoints (Razorpay Orders API, Checkout and webhooks). The rules live in app.services.payments."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.schemas.payments import (
    PaymentConfirmIn,
    PaymentConfirmOut,
    PaymentOrderIn,
    PaymentOrderOut,
)
from app.core.security import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.services import payments as svc

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/order", response_model=PaymentOrderOut)
def create_order(
    payload: PaymentOrderIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaymentOrderOut:
    return svc.create_order(db, payload.booking_id, payload.method, user)


@router.post("/{order_id}/confirm", response_model=PaymentConfirmOut)
def confirm_order(
    order_id: str,
    body: PaymentConfirmIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaymentConfirmOut:
    return svc.confirm_order(db, order_id, body, user)


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    raw = await request.body()
    return svc.handle_webhook(
        db,
        raw,
        signature=request.headers.get("X-Razorpay-Signature", ""),
        event_id=request.headers.get("X-Razorpay-Event-Id", ""),
    )
