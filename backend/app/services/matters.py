"""The matters timeline and deadline clocks for the dashboard."""

import json
from datetime import date

from sqlalchemy.orm import Session

from app.api.schemas.matters import DeadlineClock, Matter, MattersOut
from app.db.models import ChatMessage, User
from app.services import deadlines

BNS_FROM = date(2024, 7, 1)
LIMIT = 60


def _status(meta: dict) -> str:
    escalation = meta.get("escalation")
    status = meta.get("status")
    if escalation in ("emergency", "refused"):
        return escalation
    if status == "pending_review":
        return "advocate_review"
    if status == "reviewed":
        return "reviewed"
    if escalation in ("offer_lawyer", "advocate_review"):
        return "lawyer_suggested"
    return "answered"


def list_matters(db: Session, user: User, today: date | None = None) -> MattersOut:
    today = today or date.today()
    rows = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.asc()).all()
    matters: list[Matter] = []
    pending: dict[str, ChatMessage] = {}  # conversation -> question still waiting for its reply
    for row in rows:
        if row.role == "user":
            pending[row.conversation_id] = row
            continue
        question = pending.pop(row.conversation_id, None)
        if question is None:
            continue
        incident = date.fromisoformat(question.incident_date) if question.incident_date else None
        matters.append(
            Matter(
                conversation_id=row.conversation_id,
                question_id=question.id,
                question=question.text,
                asked_at=question.created_at,
                incident_date=incident,
                code=None if incident is None else ("new" if incident >= BNS_FROM else "old"),
                citation=row.citation,
                status=_status(json.loads(row.meta_json or "{}")),
            )
        )
    matters = list(reversed(matters))[:LIMIT]

    clocks: list[DeadlineClock] = []
    seen: set[tuple[str, str]] = set()
    for m in matters:
        if m.status in ("emergency", "refused"):
            continue
        rule = deadlines.match(f"{m.question} {m.citation}")
        if rule is None or (m.conversation_id, rule.title) in seen:
            continue
        seen.add((m.conversation_id, rule.title))
        due = deadlines.due_date(rule, m.incident_date) if m.incident_date else None
        clocks.append(
            DeadlineClock(
                conversation_id=m.conversation_id,
                question=m.question,
                title=rule.title,
                rule=rule.rule,
                starts=m.incident_date,
                due=due,
                days_left=(due - today).days if due else None,
            )
        )
    clocks.sort(key=lambda c: (c.due is None, c.due or today))
    return MattersOut(matters=matters, clocks=clocks)
