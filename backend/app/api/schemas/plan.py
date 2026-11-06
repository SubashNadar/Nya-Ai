"""Consult planner: a draft of the Plan screen (topic, facts, questions, goals) from the chat."""

from typing import Literal

from pydantic import BaseModel, Field

from app.api.schemas.bookings import ConsultBrief


class PlanDraftIn(BaseModel):
    conversation_id: str | None = None
    question: str | None = Field(default=None, max_length=2000)  # when there is no conversation yet


class PlanDraftOut(BaseModel):
    brief: ConsultBrief  # what the booking will carry once the user edits and confirms it
    documents: list[str]  # papers worth having ready for the call; not stored
    source: Literal["rules", "model"]
