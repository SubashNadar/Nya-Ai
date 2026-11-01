"""Per-role dashboard summaries."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.api.schemas.dashboard import (
    LawyerDashboardOut,
    RecentQuestion,
    UserDashboardOut,
)
from app.db.models import Booking, ChatMessage, Lawyer, User
from app.services.bookings import to_out, with_lawyer
from app.services.errors import Forbidden, NotFound

# Canned older examples, reproduced verbatim from the original design spec "Recent
# questions" — the demo hardcodes these two regardless of what the user actually asked.
CANNED_QUESTIONS = [
    RecentQuestion(q="Can my society stop me from keeping a pet?", when="2 days ago"),
    RecentQuestion(q="Traffic challan paid twice — refund?", when="last week"),
]

ACTIVE_BOOKING_STATUSES = ("paid", "accepted", "completed")


def relative_time(dt: datetime) -> str:
    now = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    seconds = (now - dt).total_seconds()
    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(hours // 24)
    return f"{days} day{'s' if days != 1 else ''} ago"


def user_summary(db: Session, user: User) -> UserDashboardOut:
    if user.role != "user":
        raise Forbidden("User account required")

    asked = db.query(ChatMessage).filter(ChatMessage.user_id == user.id, ChatMessage.role == "user")
    questions_answered = asked.count()

    user_bookings = (
        db.query(Booking)
        .filter(Booking.user_id == user.id, Booking.status.in_(ACTIVE_BOOKING_STATUSES))
        .order_by(Booking.created_at.desc())
        .all()
    )
    consults_booked = len(user_bookings)
    upcoming_booking = next((b for b in user_bookings if b.status in ("paid", "accepted")), None)

    recent = [
        RecentQuestion(q=msg.text, when=relative_time(msg.created_at))
        for msg in asked.order_by(ChatMessage.created_at.desc()).limit(3).all()
    ]
    recent.extend(CANNED_QUESTIONS)

    return UserDashboardOut(
        questions_answered=questions_answered,
        consults_booked=consults_booked,
        saved_amount=4500 if consults_booked else 0,
        upcoming=with_lawyer(db, upcoming_booking) if upcoming_booking is not None else None,
        recent_questions=recent[:4],
    )


def lawyer_summary(db: Session, user: User) -> LawyerDashboardOut:
    if user.role != "lawyer" or user.lawyer_id is None:
        raise Forbidden("Lawyer account required")
    lawyer = db.get(Lawyer, user.lawyer_id)
    if lawyer is None:
        raise NotFound("Lawyer not found")

    request_bookings = (
        db.query(Booking)
        .filter(
            Booking.lawyer_id == lawyer.id,
            Booking.status.in_(("pending_payment", "paid")),
        )
        .order_by(Booking.created_at.asc())
        .all()
    )
    return LawyerDashboardOut(
        earnings_month=lawyer.earnings_month,
        consultations=lawyer.consultations,
        rating=lawyer.rating,
        reviews=lawyer.reviews,
        share_pct=lawyer.share_pct,
        requests=[to_out(b, lawyer) for b in request_bookings],
    )
