"""Chat questions and history."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatMessageIn(BaseModel):
    conversation_id: str | None = None
    message: str


class ChatMeta(BaseModel):
    """How the reply was made. `mode` is "agent" (R1 graph) or "basic" (rule engine fallback)."""

    mode: str = "basic"
    status: str | None = None
    escalation: str | None = None
    risk: str | None = None
    route: str | None = None
    confidence: float | None = None
    confidence_label: str | None = None
    trace: list[str] = []
    trace_id: str | None = None
    review_id: str | None = None


class ChatMessageOut(BaseModel):
    conversation_id: str
    id: str
    text: str
    points: list[str]
    citation: str
    cta: bool
    meta: ChatMeta | None = None


class ChatMessageRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    text: str
    points: list[str]
    citation: str
    cta: bool
    meta: ChatMeta | None = None
    created_at: datetime


class ChatHistoryOut(BaseModel):
    messages: list[ChatMessageRecord]
