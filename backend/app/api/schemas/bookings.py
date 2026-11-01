"""Bookings and the consult brief."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.api.schemas.lawyers import LawyerCard


class ConsultBrief(BaseModel):
    """The consult plan the user writes before booking, shared with the advocate."""

    topic: str = Field(min_length=1, max_length=200)
    facts: str = Field(default="", max_length=4000)
    questions: list[str] = Field(default_factory=list, max_length=10)
    goals: list[str] = Field(default_factory=list, max_length=5)


class BookingIn(BaseModel):
    lawyer_id: str
    day_label: str
    slot_label: str
    consult_type: str  # "Video" | "Phone"
    brief: ConsultBrief | None = None


class BookingRespondIn(BaseModel):
    action: str  # "accept" | "decline"


class BookingOut(BaseModel):
    id: str
    ref: str
    lawyer: LawyerCard
    user_id: str
    client_name: str | None
    client_initials: str | None
    topic: str | None
    brief: ConsultBrief | None = None
    day_label: str
    slot_label: str
    consult_type: str
    fee: int
    lawyer_share: int
    status: str
    created_at: datetime


class BookingsListOut(BaseModel):
    bookings: list[BookingOut]
