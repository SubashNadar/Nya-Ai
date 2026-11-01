"""Razorpay payments: orders, checkout confirmation and webhooks.

Lawyer payouts stay manual settlement only (no Razorpay Route, linked accounts or automated
split payouts); see docs/DECISIONS.md "Real Razorpay integration". When the Razorpay keys are
unset, creating an order and the webhook raise Unavailable (503); the rest of the app works.
"""

import json
import logging

import razorpay
import razorpay.errors
from sqlalchemy.orm import Session

from app.api.schemas.payments import (
    PaymentConfirmIn,
    PaymentConfirmOut,
    PaymentOrderOut,
    PrefillOut,
)
from app.core.config import get_settings
from app.db.models import Booking, PaymentOrder, User, WebhookEvent
from app.services import bookings
from app.services.errors import (
    BadGateway,
    BadRequest,
    Forbidden,
    Invalid,
    NotFound,
    Unavailable,
)

logger = logging.getLogger(__name__)

VALID_METHODS = {"upi", "card", "netbanking"}


def _client() -> razorpay.Client:
    settings = get_settings()
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _order_out(order: PaymentOrder, user: User) -> PaymentOrderOut:
    return PaymentOrderOut(
        order_id=order.id,
        razorpay_order_id=order.razorpay_order_id,
        razorpay_key_id=get_settings().RAZORPAY_KEY_ID,
        amount=order.amount,
        currency=order.currency,
        status=order.status,
        prefill=PrefillOut(name=user.name, contact=user.phone, email=None),
    )


def _mark_paid(order: PaymentOrder, booking: Booking, payment_id: str, signature: str | None) -> None:
    """Idempotently mark an order (and its booking) as paid."""
    order.razorpay_payment_id = payment_id
    if signature is not None:
        order.razorpay_signature = signature
    order.verified = True
    order.status = "paid"
    if booking.status == "pending_payment":
        booking.status = "paid"


def create_order(db: Session, booking_id: str, method: str, user: User) -> PaymentOrderOut:
    if not get_settings().razorpay_configured:
        raise Unavailable("Payments are not configured")
    if method not in VALID_METHODS:
        raise Invalid("Invalid payment method")

    booking = bookings.get_owned(db, booking_id, user)
    if booking.status != "pending_payment":
        raise BadRequest("Booking is not awaiting payment")

    existing = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.booking_id == booking.id,
            PaymentOrder.status == "created",
            PaymentOrder.razorpay_order_id.isnot(None),
        )
        .order_by(PaymentOrder.created_at.desc())
        .first()
    )
    if existing is not None:
        existing.method = method
        db.commit()
        db.refresh(existing)
        return _order_out(existing, user)

    amount_paise = booking.fee * 100
    try:
        rzp_order = _client().order.create({"amount": amount_paise, "currency": "INR", "receipt": booking.ref})
    except Exception:  # noqa: BLE001 - any SDK/network failure surfaces as a 502
        logger.exception("Razorpay order.create failed")
        raise BadGateway("Could not reach payment gateway") from None

    order = PaymentOrder(
        booking_id=booking.id,
        method=method,
        amount=amount_paise,
        currency="INR",
        receipt=booking.ref,
        razorpay_order_id=rzp_order["id"],
        status="created",
        verified=False,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return _order_out(order, user)


def confirm_order(db: Session, order_id: str, body: PaymentConfirmIn, user: User) -> PaymentConfirmOut:
    order = db.get(PaymentOrder, order_id)
    if order is None:
        raise NotFound("Payment order not found")

    booking = db.get(Booking, order.booking_id)
    if booking is None or booking.user_id != user.id:
        raise Forbidden("Not your payment order")

    if order.verified and order.status == "paid":
        return PaymentConfirmOut(status="paid", booking=bookings.with_lawyer(db, booking))

    if body.razorpay_order_id != order.razorpay_order_id:
        raise BadRequest("Order mismatch")

    try:
        _client().utility.verify_payment_signature(
            {
                "razorpay_order_id": body.razorpay_order_id,
                "razorpay_payment_id": body.razorpay_payment_id,
                "razorpay_signature": body.razorpay_signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        raise BadRequest("Payment verification failed") from None

    _mark_paid(
        order,
        booking,
        payment_id=body.razorpay_payment_id,
        signature=body.razorpay_signature,
    )
    db.commit()
    db.refresh(order)
    db.refresh(booking)
    return PaymentConfirmOut(status=order.status, booking=bookings.with_lawyer(db, booking))


def handle_webhook(db: Session, raw: bytes, signature: str, event_id: str) -> dict:
    settings = get_settings()
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise Unavailable("Webhooks not configured")
    try:
        _client().utility.verify_webhook_signature(raw.decode(), signature, settings.RAZORPAY_WEBHOOK_SECRET)
    except razorpay.errors.SignatureVerificationError:
        raise BadRequest("Invalid webhook signature") from None

    payload = json.loads(raw)
    event = payload.get("event", "")

    if event_id and db.get(WebhookEvent, event_id):
        return {"status": "ignored"}
    if event_id:
        db.add(WebhookEvent(event_id=event_id, event_type=event))
        db.commit()

    if event in ("payment.captured", "payment.failed"):
        entity = payload["payload"]["payment"]["entity"]
        order = db.query(PaymentOrder).filter(PaymentOrder.razorpay_order_id == entity["order_id"]).first()
        if order is not None and event == "payment.captured":
            booking = db.get(Booking, order.booking_id)
            if booking is not None:
                _mark_paid(order, booking, payment_id=entity["id"], signature=None)
        elif order is not None:
            # The booking stays at pending_payment so the user can retry; see docs/DECISIONS.md.
            order.status = "failed"

    db.commit()
    return {"status": "ok"}
