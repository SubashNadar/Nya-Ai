"""Chat, /v1 and the review queue over HTTP, with the R1 graph on fake tools."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.graph import Tools
from app.agents.runner import AgentRunner, memory_checkpointer
from app.db.models import AuditLog
from app.db.seed import seed_if_empty
from app.db.session import Base, get_db
from app.main import app
from app.services import agent as agent_svc
from tests.agents.test_graph import search, sql

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)
with TestSession() as _seed:
    seed_if_empty(_seed)


def _db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(monkeypatch):
    runner = AgentRunner(Tools(search=search, sql=sql), memory_checkpointer())
    monkeypatch.setattr(agent_svc, "_runner", lambda: runner)
    monkeypatch.setitem(agent_svc._down_until, "t", 0.0)
    app.dependency_overrides[get_db] = _db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client: TestClient, phone: str, role: str = "user") -> dict:
    token = client.post("/api/auth/otp/verify", json={"phone": phone, "otp": "1234", "role": role}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_chat_answers_from_the_agent(client):
    r = client.post("/api/chat/message", json={"message": "What does BNS section 303 say?"}).json()
    assert r["meta"]["mode"] == "agent"
    assert r["meta"]["status"] == "answered"
    assert r["citation"] == "Sources: BNS §303"
    assert r["meta"]["trace"][0].startswith("Guard:")
    history = client.get("/api/chat/history", params={"conversation_id": r["conversation_id"]}).json()["messages"]
    assert history[-1]["meta"]["status"] == "answered"


def test_chat_falls_back_to_basic_mode_when_the_library_is_down(client, monkeypatch):
    down = AgentRunner(Tools(search=lambda *_: ([], False)), memory_checkpointer())
    monkeypatch.setattr(agent_svc, "_runner", lambda: down)
    r = client.post("/api/chat/message", json={"message": "Someone stole my phone, what is theft?"}).json()
    assert r["meta"]["mode"] == "basic"
    assert "Theft" in r["text"]  # the rule engine's theft answer


def test_basic_mode_never_skips_an_emergency(client, monkeypatch):
    down = AgentRunner(Tools(search=lambda *_: ([], False)), memory_checkpointer())
    monkeypatch.setattr(agent_svc, "_runner", lambda: down)
    r = client.post("/api/chat/message", json={"message": "My husband is beating me right now"}).json()
    assert r["meta"]["mode"] == "agent"
    assert r["meta"]["status"] == "emergency"


def test_review_queue_round_trip(client):
    user = _login(client, "9000000101")
    advocate = _login(client, "1234567890", role="lawyer")
    q = "My brother was arrested yesterday under BNS 303. What does the section say?"
    held = client.post("/api/chat/message", json={"message": q}, headers=user).json()
    assert held["meta"]["status"] == "pending_review"
    review_id = held["meta"]["review_id"]

    assert client.get("/api/reviews", headers=user).status_code == 403
    queue = client.get("/api/reviews", headers=advocate).json()["reviews"]
    assert review_id in [r["id"] for r in queue]
    detail = client.get(f"/api/reviews/{review_id}", headers=advocate).json()
    assert detail["draft"]["citations"][0]["section"] == "303"

    assert client.post(f"/api/reviews/{review_id}", json={"decision": "edited"}, headers=advocate).status_code == 400
    done = client.post(f"/api/reviews/{review_id}", json={"decision": "approved"}, headers=advocate).json()
    assert done["status"] == "approved"
    assert done["final"]["status"] == "reviewed"
    again = client.post(f"/api/reviews/{review_id}", json={"decision": "approved"}, headers=advocate)
    assert again.status_code == 400

    msgs = client.get("/api/chat/history", params={"conversation_id": held["conversation_id"]}, headers=user)
    last = msgs.json()["messages"][-1]
    assert last["meta"]["status"] == "reviewed"
    assert last["citation"] == "Sources: BNS §303"

    with TestSession() as db:
        events = [e.event for e in db.query(AuditLog).filter(AuditLog.conversation_id == held["conversation_id"])]
        decided = db.query(AuditLog).filter(AuditLog.event == "review_decided").first()
    assert events == ["review_queued", "review_decided"]
    assert json.loads(decided.detail_json)["decision"] == "approved"


def test_v1_answer_and_review(client):
    a = client.post("/v1/answer", json={"question": "Which BNS section replaced IPC 420?"}).json()
    assert a["status"] == "answered"
    assert a["route"] == "sql"
    assert a["latency_s"] is not None

    held = client.post("/v1/answer", json={"question": "My son was arrested today under BNS 303, what does it say?"})
    held = held.json()
    assert held["status"] == "pending_review" and held["review_id"]
    user = _login(client, "9000000102")
    body = {"thread_id": held["thread_id"], "decision": "rejected", "note": "Book a consultation."}
    assert client.post("/v1/review", json=body, headers=user).status_code == 403
    advocate = _login(client, "1234567890", role="lawyer")
    out = client.post("/v1/review", json=body, headers=advocate).json()
    assert out["status"] == "rejected"
    assert out["final"]["escalation"] == "offer_lawyer"


def test_v1_answer_never_posts_into_someone_elses_conversation(client):
    a = _login(client, "9000000103")
    mine = client.post("/api/chat/message", json={"message": "What does BNS 303 say?"}, headers=a).json()
    other = client.post("/v1/answer", json={"question": "Theft?", "conversation_id": mine["conversation_id"]})
    assert other.json()["conversation_id"] is None


def test_v1_stream_sends_node_events_then_the_answer(client):
    with client.stream("POST", "/v1/answer/stream", json={"question": "What does BNS section 303 say?"}) as r:
        body = "".join(r.iter_text())
    events = [block.split("\n")[0].removeprefix("event: ") for block in body.strip().split("\n\n")]
    assert events[0] == "node"
    assert events[-1] == "answer"
    answer = json.loads(body.strip().split("\n\n")[-1].split("data: ", 1)[1])
    assert answer["status"] == "answered"


def test_v1_health(client):
    h = client.get("/v1/health").json()
    assert h["status"] == "ok"
    assert h["agent_enabled"] is True


def test_emergency_still_handled_while_the_library_is_marked_down(client, monkeypatch):
    monkeypatch.setitem(agent_svc._down_until, "t", float("inf"))
    r = client.post("/api/chat/message", json={"message": "My husband is beating me right now"}).json()
    assert r["meta"]["status"] == "emergency"
    plain = client.post("/api/chat/message", json={"message": "What does BNS 303 say?"}).json()
    assert plain["meta"]["mode"] == "basic"
