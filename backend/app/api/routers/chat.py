"""Chat endpoints: rule-engine / Claude-backed AI answers, conversation history."""

import json
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas.chat import (
    ChatHistoryOut,
    ChatMessageIn,
    ChatMessageOut,
    ChatMessageRecord,
)
from app.core.security import get_current_user_optional
from app.db.models import ChatMessage, User
from app.db.session import get_db
from app.services.chat_engine import get_answer

router = APIRouter(prefix="/chat", tags=["chat"])


def _record_to_schema(row: ChatMessage) -> ChatMessageRecord:
    return ChatMessageRecord(
        id=row.id,
        role=row.role,
        text=row.text,
        points=json.loads(row.points),
        citation=row.citation,
        cta=row.cta,
        created_at=row.created_at,
    )


@router.post("/message", response_model=ChatMessageOut)
def send_message(
    payload: ChatMessageIn,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> ChatMessageOut:
    conversation_id = payload.conversation_id or uuid.uuid4().hex
    user_id = user.id if user else None

    db.add(
        ChatMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            text=payload.message,
            points="[]",
            citation="",
            cta=False,
        )
    )

    answer = get_answer(payload.message)
    # The static greeting ("cta: false") is rendered client-side and never round-trips
    # through this endpoint, so every real reply generated here sets cta unconditionally
    # true, per the original design spec ("every AI answer after the greeting").
    ai_message = ChatMessage(
        conversation_id=conversation_id,
        user_id=user_id,
        role="ai",
        text=answer["text"],
        points=json.dumps(answer["points"]),
        citation=answer["citation"],
        cta=True,
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    return ChatMessageOut(
        conversation_id=conversation_id,
        id=ai_message.id,
        text=ai_message.text,
        points=answer["points"],
        citation=ai_message.citation,
        cta=ai_message.cta,
    )


@router.get("/history", response_model=ChatHistoryOut)
def get_history(
    conversation_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> ChatHistoryOut:
    query = db.query(ChatMessage)
    if conversation_id:
        query = query.filter(ChatMessage.conversation_id == conversation_id)
    elif user:
        # No explicit conversation_id: fall back to the authenticated user's most
        # recent conversation (guests with no conversation_id simply get nothing yet).
        last = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user.id)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        if last is None:
            return ChatHistoryOut(messages=[])
        query = query.filter(ChatMessage.conversation_id == last.conversation_id)
    else:
        return ChatHistoryOut(messages=[])

    rows = query.order_by(ChatMessage.created_at.asc()).all()
    return ChatHistoryOut(messages=[_record_to_schema(row) for row in rows])
