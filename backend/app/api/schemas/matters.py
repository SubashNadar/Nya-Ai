"""A user's matters: every question with its incident date, plus the deadline clocks they start."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

MatterStatus = Literal["answered", "advocate_review", "reviewed", "lawyer_suggested", "emergency", "refused"]


class Matter(BaseModel):
    conversation_id: str
    question_id: str
    question: str
    asked_at: datetime
    incident_date: date | None
    # "old" = IPC, CrPC and Evidence Act era (before 1 July 2024); "new" = BNS, BNSS, BSA.
    code: Literal["old", "new"] | None
    citation: str
    status: MatterStatus


class DeadlineClock(BaseModel):
    conversation_id: str
    question: str
    title: str
    rule: str
    starts: date | None
    due: date | None
    days_left: int | None


class MattersOut(BaseModel):
    matters: list[Matter]
    clocks: list[DeadlineClock]
