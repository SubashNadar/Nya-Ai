"""The typed state that moves through the R1 graph, and the Pydantic models its nodes return.

One state object per chat turn. `thread_id` is the turn's id (not the conversation's), so an
answer held for advocate review can be resumed hours later without a newer question in the
same conversation overwriting the paused run. Chat memory comes in as `history` from the app's
own `chat_messages` table; Langfuse groups the turns of a conversation by `conversation_id`.
"""

import operator
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field

from app.rag.retrieve import Evidence

Route = Literal["none", "rag", "sql", "hybrid"]
Escalation = Literal["none", "offer_lawyer", "advocate_review", "emergency", "refused"]
Status = Literal["answered", "pending_review", "reviewed", "rejected", "emergency", "refused", "no_evidence"]


def merge_evidence(left: list | None, right: list | None) -> list:
    """Parallel researchers append; `None` from the guard resets the list for a new turn."""
    if right is None:
        return []
    return (left or []) + right


def merge_trace(left: list | None, right: list | None) -> list:
    if right is None:
        return []
    return (left or []) + right


class Citation(BaseModel):
    act: str
    section: str
    heading: str = ""


class SqlResult(BaseModel):
    template: str
    params: dict[str, Any]
    rows: Any = None
    error: str | None = None
    sections: list[tuple[str, str]] = Field(default_factory=list)  # sections the result names


class Draft(BaseModel):
    text: str
    points: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    model: str = "extractive"  # Azure deployment that wrote it, or "extractive" without a model


class Critique(BaseModel):
    verdict: Literal["pass", "retry", "escalate", "no_evidence"]
    confidence: float
    confidence_label: Literal["High", "Medium", "Low"]
    cited: list[tuple[str, str]] = Field(default_factory=list)
    unsupported: list[tuple[str, str]] = Field(default_factory=list)
    advice: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Answer(BaseModel):
    """What the agent returns for one turn: the shape `/v1/answer` sends and the chat stores."""

    status: Status
    text: str
    points: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: float | None = None
    confidence_label: str | None = None
    risk: str = "Low"
    route: Route = "rag"
    escalation: Escalation = "none"
    as_of: str | None = None
    acts_in_scope: list[str] = Field(default_factory=list)
    attacks: list[str] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)  # one line per node, for the reasoning-trace panel
    library_ok: bool = True  # False when the law library could not be reached at all

    @property
    def citation_line(self) -> str:
        if not self.citations:
            return ""
        return "Sources: " + ", ".join(f"{c.act} §{c.section}" for c in self.citations)


class NyaState(TypedDict, total=False):
    question: str  # as the user typed it; never sent to a model or a trace
    incident_date: str | None  # ISO date the user gave for the incident; wins over dates in the text
    history: list[dict]  # earlier turns, [{"role": "user"|"ai", "text": ...}], newest last
    redacted_question: str
    risk: str
    route: Route
    escalation: Escalation
    attacks: list[str]
    reasons: list[str]
    as_of: str
    acts_in_scope: list[str]
    evidence: Annotated[list[Evidence], merge_evidence]
    library_down: Annotated[bool, operator.or_]  # parallel researchers may both report
    sql_result: SqlResult | None
    draft: Draft | None
    critique: Critique | None
    attempts: int
    review: dict | None  # the advocate's decision once the pause is resumed
    answer: Answer | None
    trace: Annotated[list[str], merge_trace]
