"""Chat questions and history."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatMessageIn(BaseModel):
    conversation_id: str | None = None
    message: str


class ChatMessageOut(BaseModel):
    conversation_id: str
    id: str
    text: str
    points: list[str]
    citation: str
    cta: bool


class ChatMessageRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    text: str
    points: list[str]
    citation: str
    cta: bool
    created_at: datetime


class ChatHistoryOut(BaseModel):
    messages: list[ChatMessageRecord]
