"""Booking rules: create, list, fetch with ownership checks, and the advocate's response."""

from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas.bookings import BookingIn, BookingOut, ConsultBrief
from app.db.models import Booking, Lawyer, User
from app.services.errors import Forbidden, Invalid, NotFound
from app.services.lawyers import to_card


def to_out(booking: Booking, lawyer: Lawyer) -> BookingOut:
    return BookingOut(
        id=booking.id,
        ref=booking.ref,
        lawyer=to_card(lawyer),
        user_id=booking.user_id,
        client_name=booking.client_name,
        client_initials=booking.client_initials,
        topic=booking.topic,
        brief=ConsultBrief.model_validate_json(booking.brief_json) if booking.brief_json else None,
        day_label=booking.day_label,
        slot_label=booking.slot_label,
        consult_type=booking.consult_type,
        fee=booking.fee,
        lawyer_share=booking.lawyer_share,
        status=booking.status,
        created_at=booking.created_at,
    )


def with_lawyer(db: Session, booking: Booking) -> BookingOut:
    return to_out(booking, db.get(Lawyer, booking.lawyer_id))


def next_ref(db: Session) -> str:
    today = datetime.now(UTC).date()
    prefix = f"NX-{today:%Y%m%d}-"
    count_today = db.query(func.count(Booking.id)).filter(Booking.ref.like(f"{prefix}%")).scalar() or 0
    return f"{prefix}{count_today + 1:03d}"


def get_owned(db: Session, booking_id: str, user: User) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise NotFound("Booking not found")
    is_owner_user = user.role == "user" and booking.user_id == user.id
    is_owner_lawyer = user.role == "lawyer" and booking.lawyer_id == user.lawyer_id
    if not (is_owner_user or is_owner_lawyer):
        raise Forbidden("Not your booking")
    return booking


def create(db: Session, payload: BookingIn, user: User) -> BookingOut:
    if payload.consult_type not in ("Video", "Phone"):
        raise Invalid("Invalid consult_type")
    lawyer = db.get(Lawyer, payload.lawyer_id)
    if lawyer is None:
        raise NotFound("Lawyer not found")

    booking = Booking(
        ref=next_ref(db),
        lawyer_id=lawyer.id,
        user_id=user.id,
        client_name=user.name,
        client_initials=user.initials,
        topic=payload.brief.topic if payload.brief else None,
        brief_json=payload.brief.model_dump_json() if payload.brief else None,
        day_label=payload.day_label,
        slot_label=payload.slot_label,
        consult_type=payload.consult_type,
        fee=lawyer.price,
        lawyer_share=int(lawyer.price * lawyer.share_pct / 100),
        status="pending_payment",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return to_out(booking, lawyer)


def list_for(db: Session, user: User) -> list[BookingOut]:
    if user.role == "lawyer":
        if user.lawyer_id is None:
            return []
        query = db.query(Booking).filter(Booking.lawyer_id == user.lawyer_id)
    else:
        query = db.query(Booking).filter(Booking.user_id == user.id)
    return [with_lawyer(db, b) for b in query.order_by(Booking.created_at.desc()).all()]


def respond(db: Session, booking_id: str, action: str, user: User) -> BookingOut:
    if user.role != "lawyer":
        raise Forbidden("Lawyer account required")
    if action not in ("accept", "decline"):
        raise Invalid("Invalid action")

    booking = db.get(Booking, booking_id)
    if booking is None:
        raise NotFound("Booking not found")
    if booking.lawyer_id != user.lawyer_id:
        raise Forbidden("Not your booking")

    booking.status = "accepted" if action == "accept" else "declined"
    db.commit()
    db.refresh(booking)
    return with_lawyer(db, booking)
