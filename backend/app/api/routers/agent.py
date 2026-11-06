"""Agent service endpoints (`/v1`): cited answers from the R1 graph, streamed or whole, and review resume.

The app's chat calls the same service in process (app.services.agent.chat_reply); these routes
expose the agent on its own for the eval runner, Langflow and the advocate portal.
"""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.schemas.agent import AgentHealthOut, AnswerIn, AnswerOut, V1ReviewIn
from app.api.schemas.reviews import ReviewOut
from app.core.config import get_settings
from app.core.security import get_current_user_optional, require_lawyer
from app.db.models import User
from app.db.session import get_db
from app.services import agent as svc

router = APIRouter(prefix="/v1", tags=["agent"])


def _scope(db: Session, payload: AnswerIn, user: User | None) -> str | None:
    """Only a conversation the caller may see gets the reviewed answer posted back into it."""
    cid = payload.conversation_id
    return cid if cid and svc.may_access(db, cid, user.id if user else None) else None


def _out(result, conversation_id: str | None, review_id: str | None, latency: float | None = None) -> AnswerOut:
    a = result.answer
    return AnswerOut(
        thread_id=result.thread_id,
        conversation_id=conversation_id,
        trace_id=result.trace_id,
        review_id=review_id,
        latency_s=round(latency, 3) if latency is not None else None,
        **a.model_dump(include=set(AnswerOut.model_fields) - {"thread_id", "conversation_id", "trace_id", "review_id"}),
    )


@router.post("/answer", response_model=AnswerOut)
def answer(
    payload: AnswerIn, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)
) -> AnswerOut:
    cid = _scope(db, payload, user)
    history = [h.model_dump() for h in payload.history]
    result, queued, latency = svc.answer(db, payload.question, cid, user, history)
    db.commit()
    return _out(result, cid, queued.id if queued else None, latency)


@router.post("/answer/stream")
def answer_stream(
    payload: AnswerIn, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)
) -> StreamingResponse:
    """Server-sent events: `node` per finished graph node (the reasoning-trace panel), then `answer`."""
    cid = _scope(db, payload, user)
    history = [h.model_dump() for h in payload.history]

    def events():
        for event in svc.stream(db, payload.question, cid, user, history):
            if event["event"] == "answer":
                data = _out(event["result"], cid, event["review_id"]).model_dump_json()
                yield f"event: answer\ndata: {data}\n\n"
            else:
                yield f"event: node\ndata: {json.dumps({'node': event['node'], 'line': event['line']})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@router.post("/review", response_model=ReviewOut)
def review(payload: V1ReviewIn, db: Session = Depends(get_db), lawyer: User = Depends(require_lawyer)) -> ReviewOut:
    row = svc.review_by_thread(db, payload.thread_id)
    return ReviewOut(**svc.decide(db, row, lawyer, payload.model_dump(exclude={"thread_id"})))


@router.get("/health", response_model=AgentHealthOut)
def health() -> AgentHealthOut:
    from app.agents.llm import azure_configured
    from app.core.observability import langfuse

    s = get_settings()
    return AgentHealthOut(
        status="ok",
        agent_enabled=s.AGENT_ENABLED,
        azure=azure_configured(),
        langfuse=langfuse() is not None,
        library=svc.library_reachable(),
        checkpointer="sqlite",
    )
