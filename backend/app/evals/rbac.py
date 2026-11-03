"""SLO 13, unauthorized data access: cross-account probes against the real API on a fresh database.

Two clients (A, B), the demo lawyer (Meera) and a second lawyer try to read or change each
other's data. A probe that succeeds is a violation. The target is 0.
"""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@dataclass
class Probe:
    name: str
    violated: bool
    detail: str


def run_probes() -> list[Probe]:
    from app.db.models import Lawyer, User
    from app.db.seed import seed_if_empty
    from app.db.session import Base, get_db
    from app.main import app

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    with session() as db:
        seed_if_empty(db)
        other = db.query(Lawyer).filter(~Lawyer.name.contains("Meera")).first()
        db.add(User(role="lawyer", name=other.name, initials="OL", phone="1111122222", lawyer_id=other.id))
        db.commit()

    def _db():
        db = session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    try:
        return _probe(TestClient(app))
    finally:
        app.dependency_overrides.pop(get_db, None)


def _probe(c: TestClient) -> list[Probe]:
    def login(phone: str, role: str = "user") -> dict:
        r = c.post("/api/auth/otp/verify", json={"phone": phone, "otp": "1234", "role": role})
        return {"Authorization": f"Bearer {r.json()['token']}"}

    a, b = login("9000000101"), login("9000000102")
    meera, other_lawyer = login("1234567890", "lawyer"), login("1111122222", "lawyer")
    meera_id = next(lw["id"] for lw in c.get("/api/lawyers").json()["lawyers"] if "Meera" in lw["name"])
    brief = {"topic": "A's private topic", "facts": "A's private facts", "questions": ["q"]}
    booking = c.post(
        "/api/bookings",
        json={"lawyer_id": meera_id, "day_label": "Today", "slot_label": "11:00 AM", "consult_type": "Phone",
              "brief": brief},
        headers=a,
    ).json()  # fmt: skip
    bid = booking["id"]
    conv = c.post("/api/chat/message", json={"message": "A's private question about theft"}, headers=a).json()
    cid = conv["conversation_id"]
    thread_id = (c.get("/api/messages/threads", headers=meera).json().get("threads") or [{}])[0].get("id", "none")

    def denied(r) -> bool:
        return r.status_code in (401, 403, 404)

    def leaks_chat(r) -> bool:
        return r.status_code == 200 and any("A's private" in m.get("text", "") for m in r.json().get("messages", []))

    checks: list[tuple[str, Callable[[], bool]]] = [
        ("anonymous reads bookings", lambda: not denied(c.get("/api/bookings/me"))),
        ("B reads A's booking", lambda: not denied(c.get(f"/api/bookings/{bid}", headers=b))),
        ("B's list shows A's booking", lambda: bid in str(c.get("/api/bookings/me", headers=b).json())),
        ("B's dashboard shows A's booking", lambda: booking["ref"] in str(
            c.get("/api/dashboard/user", headers=b).json())),
        ("B pays for A's booking", lambda: not denied(
            c.post("/api/payments/order", json={"booking_id": bid, "method": "upi"}, headers=b))),
        ("client opens lawyer dashboard", lambda: not denied(c.get("/api/dashboard/lawyer", headers=a))),
        ("client lists lawyer threads", lambda: not denied(c.get("/api/messages/threads", headers=a))),
        ("client accepts own booking as lawyer", lambda: not denied(
            c.patch(f"/api/bookings/{bid}/respond", json={"action": "accept"}, headers=a))),
        ("other lawyer reads A's booking and brief", lambda: not denied(
            c.get(f"/api/bookings/{bid}", headers=other_lawyer))),
        ("other lawyer accepts Meera's booking", lambda: not denied(
            c.patch(f"/api/bookings/{bid}/respond", json={"action": "accept"}, headers=other_lawyer))),
        ("other lawyer reads Meera's thread", lambda: not denied(
            c.get(f"/api/messages/threads/{thread_id}", headers=other_lawyer))),
        ("other lawyer replies in Meera's thread", lambda: not denied(
            c.post(f"/api/messages/threads/{thread_id}/reply", json={"text": "x"}, headers=other_lawyer))),
        ("B reads A's chat by conversation id", lambda: leaks_chat(
            c.get("/api/chat/history", params={"conversation_id": cid}, headers=b))),
        ("anonymous reads A's chat by conversation id", lambda: leaks_chat(
            c.get("/api/chat/history", params={"conversation_id": cid}))),
        ("B writes into A's conversation", lambda: c.post(
            "/api/chat/message", json={"conversation_id": cid, "message": "B was here"}, headers=b
        ).json().get("conversation_id") == cid),
    ]  # fmt: skip
    out = []
    for name, check in checks:
        violated = bool(check())
        out.append(Probe(name, violated, "succeeded (violation)" if violated else "denied"))
    return out
