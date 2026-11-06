"""Answer feedback on chat replies: stored, sent to Langfuse as `user_feedback`, unsafe reports audited."""

import json
import logging

from sqlalchemy.orm import Session

from app.api.schemas.feedback import FeedbackIn, FeedbackOut
from app.db.models import AnswerFeedback, ChatMessage, User
from app.services.agent import may_access, record
from app.services.errors import BadRequest, NotFound

logger = logging.getLogger(__name__)


def give(db: Session, payload: FeedbackIn, user: User | None) -> FeedbackOut:
    msg = db.get(ChatMessage, payload.message_id)
    if msg is None or not may_access(db, msg.conversation_id, user.id if user else None):
        raise NotFound("Message not found")
    if msg.role != "ai":
        raise BadRequest("Feedback is for AI answers only")
    trace_id = (json.loads(msg.meta_json) if msg.meta_json else {}).get("trace_id")
    row = AnswerFeedback(
        message_id=msg.id,
        user_id=user.id if user else None,
        rating=payload.rating,
        reason=payload.reason,
        comment=payload.comment,
        trace_id=trace_id,
    )
    db.add(row)
    if payload.reason == "unsafe":
        record(
            db,
            "answer_reported",
            actor="user",
            conversation_id=msg.conversation_id,
            trace_id=trace_id,
            message_id=msg.id,
            comment=payload.comment,
        )
    db.commit()
    db.refresh(row)
    _score(trace_id, payload)
    return FeedbackOut(
        id=row.id, message_id=row.message_id, rating=row.rating, reason=row.reason, created_at=row.created_at
    )


def _score(trace_id: str | None, payload: FeedbackIn) -> None:
    from app.core.observability import langfuse

    client = langfuse()
    if not (trace_id and client):
        return
    try:
        client.create_score(
            trace_id=trace_id,
            name="user_feedback",
            value=1 if payload.rating == "up" else 0,
            data_type="BOOLEAN",
            comment=payload.reason,
        )
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.exception("Langfuse user_feedback score not sent")
