"""Agent service (`/v1`): one cited answer per question, streamed or not, and the review resume."""

from typing import Literal

from pydantic import BaseModel, Field

from app.api.schemas.reviews import ReviewDecisionIn


class HistoryTurn(BaseModel):
    role: Literal["user", "ai"]
    text: str = Field(max_length=4000)


class AnswerIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
    history: list[HistoryTurn] = Field(default_factory=list, max_length=12)


class CitationOut(BaseModel):
    act: str
    section: str
    heading: str = ""


class AnswerOut(BaseModel):
    thread_id: str
    conversation_id: str | None
    status: str  # answered | pending_review | reviewed | rejected | emergency | refused | no_evidence
    text: str
    points: list[str]
    citations: list[CitationOut]
    confidence: float | None
    confidence_label: str | None
    risk: str
    route: str
    escalation: str
    as_of: str | None
    acts_in_scope: list[str]
    trace: list[str]
    trace_id: str | None
    review_id: str | None
    library_ok: bool
    latency_s: float | None = None


class V1ReviewIn(ReviewDecisionIn):
    thread_id: str


class AgentHealthOut(BaseModel):
    status: str
    agent_enabled: bool
    azure: bool
    langfuse: bool
    library: bool
    checkpointer: str
