"""A consult plan sent with a booking is stored and returned to both the user and the advocate."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import seed_if_empty
from app.db.session import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)
with TestSession() as _db:
    seed_if_empty(_db)


def _db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


def _client() -> TestClient:
    app.dependency_overrides[get_db] = _db
    return TestClient(app)


def _login(client: TestClient, phone: str, role: str = "user") -> dict:
    token = client.post("/api/auth/otp/verify", json={"phone": phone, "otp": "1234", "role": role}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_brief_is_saved_and_visible_to_advocate():
    client = _client()
    user = _login(client, "9876543210")
    lawyers = client.get("/api/lawyers").json()["lawyers"]
    lawyer_id = next(lw["id"] for lw in lawyers if "Meera" in lw["name"])  # seeded with phone 1234567890
    brief = {
        "topic": "Deposit not returned",
        "facts": "Moved out 1 Sep 2026; landlord kept the deposit.",
        "questions": ["Should I send a legal notice first?"],
        "goals": ["Recover the deposit"],
    }
    created = client.post(
        "/api/bookings",
        json={
            "lawyer_id": lawyer_id,
            "day_label": "Today",
            "slot_label": "10:00 AM",
            "consult_type": "Video",
            "brief": brief,
        },
        headers=user,
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["topic"] == "Deposit not returned"
    assert body["brief"] == brief

    advocate = _login(client, "1234567890", role="lawyer")
    seen = client.get(f"/api/bookings/{body['id']}", headers=advocate)
    assert seen.status_code == 200
    assert seen.json()["brief"]["questions"] == ["Should I send a legal notice first?"]

    plain = client.post(
        "/api/bookings",
        json={"lawyer_id": lawyer_id, "day_label": "Today", "slot_label": "11:30 AM", "consult_type": "Phone"},
        headers=user,
    )
    assert plain.json()["brief"] is None
