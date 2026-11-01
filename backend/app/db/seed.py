"""Seeds the 4 demo lawyers, the canonical demo-lawyer login, 3 lawyer-portal
requests and 3 message threads — exact data from the original design spec
"""

from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.db.models import Booking, Lawyer, MessageThread, ThreadMessage, User

# bar_council_id / bio are only given in the UI reference for Meera Krishnan's profile
# screen (§10). The other three lawyers have no sourced bio/registration text anywhere
# in the demo, so a fabricated-looking bar council number would violate the guardrails'
# "never present a fabricated ... business number as if it were sourced" rule. These
# use a clearly generic placeholder instead — see docs/DECISIONS.md.
GENERIC_BAR_ID = "Bar Council verified — registration on file"


def _generic_bio(spec: str, exp: int) -> str:
    return f"{exp} years practicing {spec} in India. Bar Council verified by Nya-AI."


LAWYERS = [
    dict(
        name="Adv. Meera Krishnan",
        initials="MK",
        avatar_color="#1F3A5F",
        spec="Criminal Law",
        category="Criminal",
        exp=12,
        langs="English,Tamil",
        rating=4.9,
        reviews=312,
        next_slot="Today 6:00 PM",
        bio=(
            "12 years defending clients across Chennai's sessions and High Court. "
            "Specialist in theft, cheating (§420) and bail matters. Known for clear, "
            "jargon-free advice — most first consults end with a concrete action plan."
        ),
        bar_council_id="TN/1123/2014",
        earnings_month=42700,
        consultations=61,
    ),
    dict(
        name="Adv. Rohan Deshpande",
        initials="RD",
        avatar_color="#2F6B57",
        spec="Property & Tenancy",
        category="Property",
        exp=8,
        langs="English,Hindi,Marathi",
        rating=4.8,
        reviews=204,
        next_slot="Today 7:30 PM",
        bio=_generic_bio("Property & Tenancy", 8),
        bar_council_id=GENERIC_BAR_ID,
        earnings_month=0,
        consultations=0,
    ),
    dict(
        name="Adv. Sana Qureshi",
        initials="SQ",
        avatar_color="#8A6A2E",
        spec="Family Law",
        category="Family",
        exp=10,
        langs="English,Hindi,Urdu",
        rating=4.9,
        reviews=287,
        next_slot="Tomorrow 11:00 AM",
        bio=_generic_bio("Family Law", 10),
        bar_council_id=GENERIC_BAR_ID,
        earnings_month=0,
        consultations=0,
    ),
    dict(
        name="Adv. Arjun Nair",
        initials="AN",
        avatar_color="#52606D",
        spec="Employment & Corporate",
        category="Employment",
        exp=6,
        langs="English,Malayalam",
        rating=4.7,
        reviews=156,
        next_slot="Tomorrow 4:00 PM",
        bio=_generic_bio("Employment & Corporate", 6),
        bar_council_id=GENERIC_BAR_ID,
        earnings_month=0,
        consultations=0,
    ),
]

# Seed requests always awaiting accept/decline -> status "paid" (fee already paid;
# the lawyer dashboard's `requests` field is any pending_payment/paid booking
# awaiting accept/decline — see routers/dashboard.py).
PORTAL_REQUESTS = [
    dict(
        client_name="Priya S.",
        client_initials="PS",
        topic="Tenant deposit dispute",
        day_label="Today",
        slot_label="6:00 PM",
    ),
    dict(
        client_name="Vikram M.",
        client_initials="VM",
        topic="Cheque bounce NI Act §138",
        day_label="Tomorrow",
        slot_label="11:00 AM",
    ),
    dict(
        client_name="Anita R.",
        client_initials="AR",
        topic="Mutual consent divorce query",
        day_label="Tomorrow",
        slot_label="4:00 PM",
    ),
]

MESSAGE_THREADS = [
    dict(
        client_name="Priya S.",
        client_initials="PS",
        topic="Tenant deposit dispute",
        unread=True,
        messages=[
            (
                "client",
                "Sir, my landlord in Chennai is refusing to return my ₹50,000 deposit "
                "even 2 months after I vacated. Nya-AI told me about the Model Tenancy "
                "Act — can you help me send a legal notice?",
            ),
        ],
    ),
    dict(
        client_name="Vikram M.",
        client_initials="VM",
        topic="Cheque bounce (NI Act §138)",
        unread=True,
        messages=[
            (
                "client",
                "A cheque of ₹1.2L issued to me bounced twice. What are my next steps "
                "before the 30-day notice window closes?",
            ),
        ],
    ),
    dict(
        client_name="Anita R.",
        client_initials="AR",
        topic="Mutual consent divorce",
        unread=False,
        messages=[
            (
                "client",
                "We both agree to separate amicably. How long will mutual consent "
                "divorce take, and which documents should we prepare?",
            ),
            (
                "lawyer",
                "With mutual consent and 1 year of separation, expect 6–12 months. "
                "Start collecting: marriage certificate, address proofs, and a draft "
                "settlement on maintenance and assets. We can cover details on our call.",
            ),
        ],
    ),
]


def _make_ref(seq: int, on: date | None = None) -> str:
    on = on or datetime.now(UTC).date()
    return f"NX-{on:%Y%m%d}-{seq:03d}"


def seed_if_empty(db: Session) -> None:
    if db.query(Lawyer).first() is not None:
        return  # already seeded

    lawyers_by_category: dict[str, Lawyer] = {}
    for data in LAWYERS:
        lawyer = Lawyer(**data)
        db.add(lawyer)
        lawyers_by_category[data["category"]] = lawyer
    db.flush()  # assign ids

    meera = lawyers_by_category["Criminal"]

    # Canonical demo-lawyer login identity, linked to Meera — the portal header is
    # hardcoded to "Adv. Meera Krishnan · Criminal Law · Bar Council TN/1123/2014" in
    # the UI reference (§8), so both "Explore as demo lawyer" and any phone/OTP login
    # taken with role=lawyer resolve to this same account. See docs/DECISIONS.md.
    demo_lawyer_user = User(
        role="lawyer",
        name=meera.name,
        initials=meera.initials,
        # User-supplied demo number so lawyer-OTP login (role="lawyer") is actually
        # reachable end-to-end, not just a correct-but-unreachable code path — see
        # docs/DECISIONS.md "Resolution pass with user, 2026-07-18".
        phone="1234567890",
        lawyer_id=meera.id,
    )
    db.add(demo_lawyer_user)

    for i, req in enumerate(PORTAL_REQUESTS, start=1):
        client_user = User(
            role="user",
            name=req["client_name"],
            initials=req["client_initials"],
            phone=None,
        )
        db.add(client_user)
        db.flush()
        db.add(
            Booking(
                ref=_make_ref(i),
                lawyer_id=meera.id,
                user_id=client_user.id,
                client_name=req["client_name"],
                client_initials=req["client_initials"],
                topic=req["topic"],
                day_label=req["day_label"],
                slot_label=req["slot_label"],
                consult_type="Video",
                fee=500,
                lawyer_share=350,
                status="paid",
            )
        )

    for thread_data in MESSAGE_THREADS:
        thread = MessageThread(
            lawyer_id=meera.id,
            client_name=thread_data["client_name"],
            client_initials=thread_data["client_initials"],
            topic=thread_data["topic"],
            unread=thread_data["unread"],
        )
        db.add(thread)
        db.flush()
        for sender, text in thread_data["messages"]:
            db.add(ThreadMessage(thread_id=thread.id, sender=sender, text=text))

    db.commit()
