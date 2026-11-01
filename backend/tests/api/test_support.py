"""The public Contact form endpoint stores a message and returns a reference, with no login."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)


def _db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


def _client() -> TestClient:
    app.dependency_overrides[get_db] = _db
    return TestClient(app)


def test_support_message_gets_daily_ref():
    client = _client()
    body = {"name": "Asha", "contact": "asha@example.com", "topic": "booking", "text": "My refund has not arrived yet."}
    first = client.post("/api/support", json=body)
    second = client.post("/api/support", json=body)
    assert first.status_code == 201
    assert first.json()["ref"].startswith("SUP-") and first.json()["ref"].endswith("-001")
    assert second.json()["ref"].endswith("-002")


def test_support_message_rejects_short_text_and_unknown_topic():
    client = _client()
    assert (
        client.post("/api/support", json={"name": "A", "contact": "a@b.c", "topic": "other", "text": "hi"}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/support", json={"name": "A", "contact": "a@b.c", "topic": "sales", "text": "long enough text"}
        ).status_code
        == 422
    )
