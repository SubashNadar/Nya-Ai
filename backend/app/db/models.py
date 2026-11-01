"""SQLAlchemy ORM models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def gen_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    role: Mapped[str] = mapped_column(String(16))  # "user" | "lawyer"
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    initials: Mapped[str] = mapped_column(String(4), default="U")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    # Set only for role="lawyer" accounts, linking the login identity to a seeded
    # Lawyer row (the demo only ever exposes one lawyer-portal persona: Meera Krishnan).
    lawyer_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("lawyers.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    lawyer: Mapped["Lawyer | None"] = relationship(back_populates="account")


class Lawyer(Base):
    __tablename__ = "lawyers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(120))
    initials: Mapped[str] = mapped_column(String(4))
    avatar_color: Mapped[str] = mapped_column(String(16))
    spec: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40))
    exp: Mapped[int] = mapped_column(Integer)
    langs: Mapped[str] = mapped_column(String(200))  # comma-separated
    rating: Mapped[float] = mapped_column(Float)
    reviews: Mapped[int] = mapped_column(Integer)
    next_slot: Mapped[str] = mapped_column(String(60))
    bio: Mapped[str] = mapped_column(Text)
    bar_council_id: Mapped[str] = mapped_column(String(80))
    price: Mapped[int] = mapped_column(Integer, default=500)
    price_struck: Mapped[int] = mapped_column(Integer, default=5000)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    earnings_month: Mapped[int] = mapped_column(Integer, default=0)
    consultations: Mapped[int] = mapped_column(Integer, default=0)
    share_pct: Mapped[int] = mapped_column(Integer, default=70)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    account: Mapped["User | None"] = relationship(back_populates="lawyer", uselist=False)

    @property
    def langs_list(self) -> list[str]:
        return [lang.strip() for lang in self.langs.split(",") if lang.strip()]


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    conversation_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("users.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(8))  # "user" | "ai"
    text: Mapped[str] = mapped_column(Text)
    points: Mapped[str] = mapped_column(Text, default="[]")  # JSON-encoded list[str]
    citation: Mapped[str] = mapped_column(String(200), default="")
    cta: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    ref: Mapped[str] = mapped_column(String(40))
    lawyer_id: Mapped[str] = mapped_column(String(32), ForeignKey("lawyers.id"))
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    client_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    client_initials: Mapped[str | None] = mapped_column(String(4), nullable=True)
    # Set from the consult plan's topic when the user plans the call first; the 3 seeded
    # lawyer-portal demo requests also carry one.
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Consult plan as JSON (facts, questions, goals), shared with the advocate. Null when skipped.
    brief_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    day_label: Mapped[str] = mapped_column(String(40))
    slot_label: Mapped[str] = mapped_column(String(20))
    consult_type: Mapped[str] = mapped_column(String(10))  # "Video" | "Phone"
    fee: Mapped[int] = mapped_column(Integer, default=500)
    lawyer_share: Mapped[int] = mapped_column(Integer, default=350)
    status: Mapped[str] = mapped_column(String(20), default="pending_payment")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    lawyer: Mapped["Lawyer"] = relationship()


class PaymentOrder(Base):
    """Real Razorpay order (see routers/payments.py). Replaces the earlier simulated
    version — see docs/DECISIONS.md "Real Razorpay integration" entry.
    """

    __tablename__ = "payment_orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    booking_id: Mapped[str] = mapped_column(String(32), ForeignKey("bookings.id"))
    # Advisory only now — no longer collects payment data itself; passed to Razorpay
    # Checkout as `prefill.method` so the pre-existing method-picker screen still has
    # a real function. "upi" | "card" | "netbanking".
    method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # NOTE: unit change — this is now in PAISE (₹500 = 50000), matching what Razorpay's
    # API expects, not rupees like the old simulated field.
    amount: Mapped[int] = mapped_column(Integer, default=50000)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    # Our reference sent to Razorpay as `receipt` — reuses booking.ref.
    receipt: Mapped[str] = mapped_column(String(64))
    razorpay_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    razorpay_signature: Mapped[str | None] = mapped_column(String(256), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="created")  # "created"|"paid"|"failed"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WebhookEvent(Base):
    """One row per processed Razorpay webhook event, keyed by their X-Razorpay-Event-Id
    header — makes webhook delivery (which Razorpay retries) idempotent.
    """

    __tablename__ = "webhook_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(40))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MessageThread(Base):
    """Lawyer <-> client message thread (Lawyer Messages screen).

    Exposed via routers/messages.py (added during the frontend build to cover a gap
    in the original endpoint plan; see docs/DECISIONS.md).
    """

    __tablename__ = "message_threads"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    lawyer_id: Mapped[str] = mapped_column(String(32), ForeignKey("lawyers.id"))
    client_name: Mapped[str] = mapped_column(String(120))
    client_initials: Mapped[str] = mapped_column(String(4))
    topic: Mapped[str] = mapped_column(String(200))
    unread: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ThreadMessage(Base):
    __tablename__ = "thread_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    thread_id: Mapped[str] = mapped_column(String(32), ForeignKey("message_threads.id"))
    sender: Mapped[str] = mapped_column(String(10))  # "client" | "lawyer"
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RevokedToken(Base):
    """Server-side logout invalidation: one row per revoked JWT (by its `jti` claim).

    Lets `POST /api/auth/logout` take effect immediately even though JWTs are
    otherwise stateless — see docs/DECISIONS.md "Resolution pass with
    user, 2026-07-18" (#9). Expired rows are pruned on logout and on app startup so
    the table stays bounded without a cron job.
    """

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SupportMessage(Base):
    """A message sent from the public Contact page. Read by the team; no reply is automated."""

    __tablename__ = "support_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    ref: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    contact: Mapped[str] = mapped_column(String(120))  # email or phone, as typed
    topic: Mapped[str] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
