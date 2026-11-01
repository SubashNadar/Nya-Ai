"""User and advocate dashboards."""

from pydantic import BaseModel

from app.api.schemas.bookings import BookingOut


class RecentQuestion(BaseModel):
    q: str
    when: str


class UserDashboardOut(BaseModel):
    questions_answered: int
    consults_booked: int
    saved_amount: int
    upcoming: BookingOut | None
    recent_questions: list[RecentQuestion]


class LawyerDashboardOut(BaseModel):
    earnings_month: int
    consultations: int
    rating: float
    reviews: int
    share_pct: int
    requests: list[BookingOut]
