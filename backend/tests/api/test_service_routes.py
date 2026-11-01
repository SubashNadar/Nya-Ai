"""Routers delegate to app.services; errors keep their status codes and {"detail": ...} shape."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.seed import seed_if_empty
from app.db.session import Base, get_db
from app.main import app

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


def _client() -> TestClient:
    app.dependency_overrides[get_db] = _db
    return TestClient(app)


def _login(client: TestClient, phone: str, role: str = "user") -> dict:
    token = client.post("/api/auth/otp/verify", json={"phone": phone, "otp": "1234", "role": role}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _meera(client: TestClient) -> str:
    return next(lw["id"] for lw in client.get("/api/lawyers").json()["lawyers"] if "Meera" in lw["name"])


def _book(client: TestClient, headers: dict) -> dict:
    r = client.post(
        "/api/bookings",
        json={"lawyer_id": _meera(client), "day_label": "Today", "slot_label": "11:00 AM", "consult_type": "Phone"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_booking_errors_keep_status_and_detail():
    client = _client()
    user = _login(client, "9000000001")
    bad = client.post(
        "/api/bookings",
        json={"lawyer_id": _meera(client), "day_label": "Today", "slot_label": "1 PM", "consult_type": "Fax"},
        headers=user,
    )
    assert bad.status_code == 422 and bad.json() == {"detail": "Invalid consult_type"}
    missing = client.get("/api/bookings/does-not-exist", headers=user)
    assert missing.status_code == 404 and missing.json() == {"detail": "Booking not found"}

    booking = _book(client, user)
    stranger = _login(client, "9000000002")
    assert client.get(f"/api/bookings/{booking['id']}", headers=stranger).status_code == 403
    assert (
        client.patch(f"/api/bookings/{booking['id']}/respond", json={"action": "accept"}, headers=user).status_code
        == 403
    )


def test_booking_flow_and_dashboards():
    client = _client()
    user = _login(client, "9000000003")
    booking = _book(client, user)
    assert booking["status"] == "pending_payment"
    assert booking["ref"].startswith("NX-")
    mine = client.get("/api/bookings/me", headers=user).json()["bookings"]
    assert [b["id"] for b in mine] == [booking["id"]]

    advocate = _login(client, "1234567890", role="lawyer")
    lawyer_dash = client.get("/api/dashboard/lawyer", headers=advocate)
    assert lawyer_dash.status_code == 200
    assert booking["id"] in [b["id"] for b in lawyer_dash.json()["requests"]]
    accepted = client.patch(f"/api/bookings/{booking['id']}/respond", json={"action": "accept"}, headers=advocate)
    assert accepted.json()["status"] == "accepted"

    user_dash = client.get("/api/dashboard/user", headers=user)
    assert user_dash.status_code == 200
    body = user_dash.json()
    assert body["consults_booked"] == 1 and body["upcoming"]["id"] == booking["id"]
    assert len(body["recent_questions"]) <= 4
    assert client.get("/api/dashboard/user", headers=advocate).status_code == 403
    assert client.get("/api/dashboard/lawyer", headers=user).status_code == 403


def test_payments_without_keys_return_503(monkeypatch):
    for key in ("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET"):
        monkeypatch.setattr(get_settings(), key, "", raising=False)
    client = _client()
    user = _login(client, "9000000004")
    booking = _book(client, user)
    r = client.post("/api/payments/order", json={"booking_id": booking["id"], "method": "upi"}, headers=user)
    assert r.status_code == 503 and r.json() == {"detail": "Payments are not configured"}
    assert client.post("/api/payments/webhook", content=b"{}").status_code == 503
    gone = client.post(
        "/api/payments/nope/confirm",
        json={"razorpay_payment_id": "p", "razorpay_order_id": "o", "razorpay_signature": "s"},
        headers=user,
    )
    assert gone.status_code == 404
