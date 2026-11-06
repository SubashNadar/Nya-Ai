"""Answer feedback, the consult planner and law library admin over HTTP (no Postgres, no Azure)."""

import pytest
from fastapi.testclient import TestClient

from app.db.models import AnswerFeedback, AuditLog
from tests.api.test_agent_routes import TestSession, _login
from tests.api.test_agent_routes import client as agent_client  # noqa: F401  # pylint: disable=unused-import


@pytest.fixture
def client(agent_client):  # noqa: F811  # pylint: disable=redefined-outer-name
    return agent_client


def _ask(client: TestClient, headers: dict | None = None, message: str = "What does BNS section 303 say?") -> dict:
    return client.post("/api/chat/message", json={"message": message}, headers=headers or {}).json()


def test_feedback_on_an_answer(client):
    user = _login(client, "9000000201")
    reply = _ask(client, user)
    up = client.post("/api/chat/feedback", json={"message_id": reply["id"], "rating": "up"}, headers=user)
    assert up.status_code == 201
    report = {"message_id": reply["id"], "rating": "down", "reason": "unsafe", "comment": "Looks like advice."}
    assert client.post("/api/chat/feedback", json=report, headers=user).status_code == 201
    with TestSession() as db:
        assert db.query(AnswerFeedback).filter(AnswerFeedback.message_id == reply["id"]).count() == 2
        assert db.query(AuditLog).filter(AuditLog.event == "answer_reported").count() >= 1


def test_feedback_only_on_your_own_ai_answers(client):
    owner = _login(client, "9000000202")
    stranger = _login(client, "9000000203")
    reply = _ask(client, owner)
    body = {"message_id": reply["id"], "rating": "down", "reason": "wrong"}
    assert client.post("/api/chat/feedback", json=body, headers=stranger).status_code == 404
    history = client.get("/api/chat/history", params={"conversation_id": reply["conversation_id"]}, headers=owner)
    question_id = history.json()["messages"][0]["id"]
    body = {"message_id": question_id, "rating": "up"}
    assert client.post("/api/chat/feedback", json=body, headers=owner).status_code == 400


def test_plan_draft_from_the_conversation(client):
    user = _login(client, "9000000204")
    reply = _ask(client, user, "My landlord kept my deposit after I moved out. Can I get it back?")
    draft = client.post("/api/plan/draft", json={"conversation_id": reply["conversation_id"]}, headers=user).json()
    assert draft["source"] == "rules"
    assert draft["brief"]["topic"].startswith("My landlord kept my deposit")
    assert "Rent or lease agreement" in draft["documents"]
    assert draft["brief"]["questions"] == ["My landlord kept my deposit after I moved out. Can I get it back?"]
    other = _login(client, "9000000205")
    denied = client.post("/api/plan/draft", json={"conversation_id": reply["conversation_id"]}, headers=other)
    assert denied.status_code == 400
    assert client.post("/api/plan/draft", json={}).status_code == 400


def test_library_admin_is_for_advocates_and_reports_what_is_missing(client):
    user = _login(client, "9000000206")
    assert client.get("/api/library/acts", headers=user).status_code == 403
    advocate = _login(client, "1234567890", role="lawyer")
    lib = client.get("/api/library/acts", headers=advocate).json()
    assert [a["code"] for a in lib["acts"]] == ["BNS", "BNSS", "BSA", "IPC"]
    assert lib["azure"] is False
    started = client.post("/api/library/ingest", json={"acts": ["BNS"]}, headers=advocate)
    assert started.status_code == 503  # no Azure here, so nothing starts
    assert client.post("/api/library/ingest", json={"acts": ["XYZ"]}, headers=advocate).status_code == 422
