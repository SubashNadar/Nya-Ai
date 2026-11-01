"""The advocate inbox."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender: str  # "client" | "lawyer"
    text: str
    created_at: datetime


class MessageThreadOut(BaseModel):
    id: str
    client_name: str
    client_initials: str
    topic: str
    unread: bool
    messages: list[MessageOut]


class MessageThreadsListOut(BaseModel):
    threads: list[MessageThreadOut]


class ThreadReplyIn(BaseModel):
    text: str


class ThreadReplyOut(BaseModel):
    message: MessageOut
