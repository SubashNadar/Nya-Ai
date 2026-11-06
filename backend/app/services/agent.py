"""The agent behind chat and `/v1`: run a turn, queue advocate reviews, record the audit log.

Routers stay HTTP only. A turn that the graph holds for an advocate becomes an `AnswerReview`
row; every escalation, refusal and advocate decision becomes an append-only `AuditLog` row with
the Langfuse trace id.
"""

import json
import logging
import time
import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AnswerReview, AuditLog, ChatMessage, User, utcnow
from app.services.errors import BadRequest, NotFound, Unavailable

logger = logging.getLogger(__name__)

DECISIONS = ("approved", "edited", "rejected")
_DOWN_FOR_S = 30.0  # after the library is found unreachable, skip the agent for this long
_down_until: dict[str, float] = {"t": 0.0}


def _runner():
    from app.agents.runner import get_runner

    return get_runner()


def record(
    db: Session, event: str, *, actor: str = "agent", conversation_id=None, thread_id=None, trace_id=None, **detail
):
    db.add(
        AuditLog(
            event=event,
            conversation_id=conversation_id,
            thread_id=thread_id,
            actor=actor,
            detail_json=json.dumps(detail, default=str),
            trace_id=trace_id,
        )
    )


def _after_turn(db: Session, result, conversation_id: str | None, user_id: str | None):
    """Queue a review and write the audit rows for one finished (or paused) turn."""
    a = result.answer
    review = None
    if result.review is not None:
        review = AnswerReview(
            thread_id=result.thread_id,
            conversation_id=conversation_id,
            user_id=user_id,
            question=result.review.get("question", ""),
            draft_json=json.dumps({"draft": result.review.get("draft"), "critique": result.review.get("critique")}),
            trace_id=result.trace_id,
        )
        db.add(review)
        db.flush()
        record(
            db,
            "review_queued",
            conversation_id=conversation_id,
            thread_id=result.thread_id,
            trace_id=result.trace_id,
            review_id=review.id,
            risk=a.risk,
        )
    elif a.escalation in ("emergency", "refused", "offer_lawyer"):
        record(
            db,
            a.escalation,
            conversation_id=conversation_id,
            thread_id=result.thread_id,
            trace_id=result.trace_id,
            risk=a.risk,
            attacks=a.attacks,
            status=a.status,
        )
    return review


def answer(
    db: Session,
    question: str,
    conversation_id: str | None,
    user: User | None,
    history=None,
    incident_date: str | None = None,
):
    """One agent turn. Returns (TurnResult, AnswerReview | None, latency in seconds)."""
    thread_id = uuid.uuid4().hex
    start = time.perf_counter()
    result = _runner().run(question, thread_id, conversation_id, user.id if user else None, history, incident_date)
    review = _after_turn(db, result, conversation_id, user.id if user else None)
    return result, review, time.perf_counter() - start


def stream(db: Session, question: str, conversation_id: str | None, user: User | None, history=None):
    """Node events, then the answer event with the review id when one was queued."""
    thread_id = uuid.uuid4().hex
    for event in _runner().stream(question, thread_id, conversation_id, user.id if user else None, history):
        if event["event"] != "answer":
            yield event
            continue
        result = event["result"]
        review = _after_turn(db, result, conversation_id, user.id if user else None)
        db.commit()
        yield {"event": "answer", "result": result, "review_id": review.id if review else None}


def library_reachable() -> bool:
    """True when the law tables in Postgres answer a trivial query."""
    from sqlalchemy import text

    from app.agents.graph import law_engine

    try:
        with law_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        return False


# ---------- chat ----------


def chat_reply(
    db: Session, message: str, conversation_id: str, user: User | None, incident_date: str | None = None
) -> dict:
    """The chat's AI reply: the agent when it can answer, the rule engine ("basic mode") when not.

    Emergencies and refusals are decided by rules that need no library or model, so the agent
    always handles them, even while the library is down; only ordinary questions fall back.
    """
    from app.agents.triage import triage
    from app.services.chat_engine import get_answer

    rules = triage(message)
    must_run = rules.escalation in ("emergency", "refused")
    library_up = time.monotonic() >= _down_until["t"]
    if get_settings().AGENT_ENABLED and (library_up or must_run):
        try:
            result, review, latency = answer(
                db, message, conversation_id, user, _history(db, conversation_id), incident_date
            )
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught  # rule engine still answers
            logger.exception("agent failed; using the rule engine")
            result = None
        if result is not None:
            a = result.answer
            if a.status != "no_evidence" or a.library_ok:
                meta = {
                    "mode": "agent",
                    "status": a.status,
                    "escalation": a.escalation,
                    "risk": a.risk,
                    "route": a.route,
                    "confidence": a.confidence,
                    "confidence_label": a.confidence_label,
                    "trace": a.trace,
                    "trace_id": result.trace_id,
                    "thread_id": result.thread_id,
                    "review_id": review.id if review else None,
                    "latency_s": round(latency, 3),
                }
                return {"text": a.text, "points": a.points, "citation": a.citation_line[:200], "meta": meta}
            _down_until["t"] = time.monotonic() + _DOWN_FOR_S
    if rules.escalation in ("offer_lawyer", "advocate_review"):
        record(db, "offer_lawyer", conversation_id=conversation_id, risk=rules.risk, mode="basic")
    basic = get_answer(message)
    meta = {"mode": "basic", "escalation": rules.escalation, "risk": rules.risk, "route": rules.route}
    return {"text": basic["text"], "points": basic["points"], "citation": basic["citation"], "meta": meta}


def may_access(db: Session, conversation_id: str, user_id: str | None) -> bool:
    """A signed-in user's conversation belongs to that user only; a guest conversation to whoever holds its id."""
    owners = {
        row[0]
        for row in db.query(ChatMessage.user_id).filter(ChatMessage.conversation_id == conversation_id).distinct()
    }
    owners.discard(None)
    return not owners or owners == {user_id}


def _history(db: Session, conversation_id: str, turns: int = 6) -> list[dict]:
    db.flush()
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(turns + 1)
        .all()
    )
    # The newest row is the question being answered (already added to the session).
    return [{"role": r.role, "text": r.text} for r in reversed(rows[1:])]


# ---------- advocate reviews ----------


def review_out(r: AnswerReview) -> dict:
    data = json.loads(r.draft_json or "{}")
    return {
        "id": r.id,
        "thread_id": r.thread_id,
        "conversation_id": r.conversation_id,
        "question": r.question,
        "draft": data.get("draft"),
        "critique": data.get("critique"),
        "status": r.status,
        "decided_by": r.decided_by,
        "final": json.loads(r.final_json) if r.final_json else None,
        "trace_id": r.trace_id,
        "created_at": r.created_at,
        "decided_at": r.decided_at,
    }


def list_reviews(db: Session, status: str | None = "pending") -> list[dict]:
    q = db.query(AnswerReview)
    if status:
        q = q.filter(AnswerReview.status == status)
    return [review_out(r) for r in q.order_by(AnswerReview.created_at.asc()).all()]


def get_review(db: Session, review_id: str) -> AnswerReview:
    review = db.get(AnswerReview, review_id)
    if review is None:
        raise NotFound("Review not found")
    return review


def review_by_thread(db: Session, thread_id: str) -> AnswerReview:
    review = db.query(AnswerReview).filter(AnswerReview.thread_id == thread_id).first()
    if review is None:
        raise NotFound("Review not found")
    return review


def decide(db: Session, review: AnswerReview, lawyer: User, decision: dict) -> dict:
    """Resume the paused run with the advocate's decision and post the result into the chat."""
    if decision.get("decision") not in DECISIONS:
        raise BadRequest("decision must be approved, edited or rejected")
    if decision["decision"] == "edited" and not decision.get("text"):
        raise BadRequest("an edited answer needs text")
    if review.status != "pending":
        raise BadRequest(f"Review already {review.status}")
    try:
        result = _runner().resume(review.thread_id, decision)
    except LookupError as e:
        raise Unavailable("The paused answer is no longer available to resume") from e

    a = result.answer
    review.status = decision["decision"]
    review.decided_by = lawyer.lawyer_id
    review.decided_at = utcnow()
    review.final_json = a.model_dump_json()
    if review.conversation_id:
        db.add(
            ChatMessage(
                conversation_id=review.conversation_id,
                user_id=review.user_id,
                role="ai",
                text=a.text,
                points=json.dumps(a.points),
                citation=a.citation_line[:200],
                cta=True,
                meta_json=json.dumps(
                    {
                        "mode": "agent",
                        "status": a.status,
                        "escalation": a.escalation,
                        "confidence": a.confidence,
                        "review_id": review.id,
                        "trace_id": review.trace_id,
                    }
                ),
            )
        )
    record(
        db,
        "review_decided",
        actor=f"lawyer:{lawyer.lawyer_id}",
        conversation_id=review.conversation_id,
        thread_id=review.thread_id,
        trace_id=review.trace_id,
        review_id=review.id,
        decision=decision["decision"],
        note=decision.get("note"),
    )
    _score_decision(review.trace_id, decision["decision"])
    db.commit()
    db.refresh(review)
    return review_out(review)


def _score_decision(trace_id: str | None, decision: str) -> None:
    from app.core.observability import langfuse

    client = langfuse()
    if not (trace_id and client):
        return
    try:
        client.create_score(trace_id=trace_id, name="advocate_decision", value=decision, data_type="CATEGORICAL")
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.exception("Langfuse advocate_decision score not sent")
