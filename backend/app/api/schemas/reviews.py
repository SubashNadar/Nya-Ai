"""Advocate review queue: answers the agent holds for a verified advocate before the user sees them."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReviewDecisionIn(BaseModel):
    decision: Literal["approved", "edited", "rejected"]
    text: str | None = Field(default=None, max_length=4000)  # required when edited
    points: list[str] | None = None
    note: str | None = Field(default=None, max_length=1000)  # shown to the user when rejected


class ReviewOut(BaseModel):
    id: str
    thread_id: str
    conversation_id: str | None
    question: str
    draft: dict | None
    critique: dict | None
    status: str
    decided_by: str | None
    final: dict | None
    trace_id: str | None
    created_at: datetime
    decided_at: datetime | None


class ReviewsListOut(BaseModel):
    reviews: list[ReviewOut]
