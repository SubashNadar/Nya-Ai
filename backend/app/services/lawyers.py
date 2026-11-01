"""Advocate directory: turning a Lawyer row into its API card."""

from app.api.schemas.lawyers import LawyerCard
from app.db.models import Lawyer


def to_card(lawyer: Lawyer) -> LawyerCard:
    return LawyerCard(
        id=lawyer.id,
        name=lawyer.name,
        initials=lawyer.initials,
        avatar_color=lawyer.avatar_color,
        spec=lawyer.spec,
        category=lawyer.category,
        exp=lawyer.exp,
        langs=lawyer.langs_list,
        rating=lawyer.rating,
        reviews=lawyer.reviews,
        next_slot=lawyer.next_slot,
    )
