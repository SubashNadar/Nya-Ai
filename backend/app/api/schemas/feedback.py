"""Answer feedback: thumbs up or down and "Report this answer" on an AI reply."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    message_id: str
    rating: Literal["up", "down"]
    reason: Literal["wrong", "unclear", "unsafe", "other"] | None = None  # for "down" and reports
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackOut(BaseModel):
    id: str
    message_id: str
    rating: str
    reason: str | None
    created_at: datetime
