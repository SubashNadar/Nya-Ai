"""Lawyer inbox (Lawyer Messages screen) endpoints.

Not in the original endpoint plan — added by the frontend build and implemented here to
match; see docs/DECISIONS.md "Messages endpoints missing from the API contract".
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.messages import (
    MessageOut,
    MessageThreadOut,
    MessageThreadsListOut,
    ThreadReplyIn,
    ThreadReplyOut,
)
from app.core.security import get_current_user
from app.db.models import MessageThread, ThreadMessage, User
from app.db.session import get_db

router = APIRouter(prefix="/messages", tags=["messages"])


def _to_out(thread: MessageThread, messages: list[ThreadMessage]) -> MessageThreadOut:
    return MessageThreadOut(
        id=thread.id,
        client_name=thread.client_name,
        client_initials=thread.client_initials,
        topic=thread.topic,
        unread=thread.unread,
        messages=[MessageOut.model_validate(m) for m in messages],
    )


def _require_lawyer_thread(db: Session, thread_id: str, user: User) -> MessageThread:
    if user.role != "lawyer" or user.lawyer_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Lawyer account required")
    thread = db.get(MessageThread, thread_id)
    if thread is None or thread.lawyer_id != user.lawyer_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return thread


@router.get("/threads", response_model=MessageThreadsListOut)
def list_threads(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> MessageThreadsListOut:
    if user.role != "lawyer" or user.lawyer_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Lawyer account required")
    threads = (
        db.query(MessageThread)
        .filter(MessageThread.lawyer_id == user.lawyer_id)
        .order_by(MessageThread.created_at.asc())
        .all()
    )
    out = []
    for thread in threads:
        msgs = (
            db.query(ThreadMessage)
            .filter(ThreadMessage.thread_id == thread.id)
            .order_by(ThreadMessage.created_at.asc())
            .all()
        )
        out.append(_to_out(thread, msgs))
    return MessageThreadsListOut(threads=out)


@router.get("/threads/{thread_id}", response_model=MessageThreadOut)
def get_thread(
    thread_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> MessageThreadOut:
    thread = _require_lawyer_thread(db, thread_id, user)
    msgs = (
        db.query(ThreadMessage)
        .filter(ThreadMessage.thread_id == thread.id)
        .order_by(ThreadMessage.created_at.asc())
        .all()
    )
    return _to_out(thread, msgs)


@router.patch("/threads/{thread_id}/read", response_model=MessageThreadOut)
def mark_thread_read(
    thread_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> MessageThreadOut:
    thread = _require_lawyer_thread(db, thread_id, user)
    thread.unread = False
    db.commit()
    db.refresh(thread)
    msgs = (
        db.query(ThreadMessage)
        .filter(ThreadMessage.thread_id == thread.id)
        .order_by(ThreadMessage.created_at.asc())
        .all()
    )
    return _to_out(thread, msgs)


@router.post("/threads/{thread_id}/reply", response_model=ThreadReplyOut)
def reply_to_thread(
    thread_id: str,
    payload: ThreadReplyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ThreadReplyOut:
    thread = _require_lawyer_thread(db, thread_id, user)
    if not payload.text.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Reply text required")

    message = ThreadMessage(thread_id=thread.id, sender="lawyer", text=payload.text)
    db.add(message)
    db.commit()
    db.refresh(message)
    return ThreadReplyOut(message=MessageOut.model_validate(message))
