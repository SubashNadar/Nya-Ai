"""The contact form."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SupportIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    contact: str = Field(min_length=3, max_length=120)
    topic: Literal["booking", "answer", "privacy", "advocate", "other"]
    text: str = Field(min_length=10, max_length=2000)


class SupportOut(BaseModel):
    ref: str
    created_at: datetime
