"""Matters timeline and deadline clocks over HTTP (no Postgres, no Azure)."""

from datetime import date, timedelta

import pytest

from app.services.deadlines import add_years, match
from tests.api.test_agent_routes import _login
from tests.api.test_agent_routes import client as agent_client  # noqa: F401  # pylint: disable=unused-import


@pytest.fixture
def client(agent_client):  # noqa: F811  # pylint: disable=redefined-outer-name
    return agent_client


def _ask(client, headers, message, incident=None):
    body = {"message": message}
    if incident:
        body["incident_date"] = incident
    return client.post("/api/chat/message", json=body, headers=headers)


def test_incident_date_decides_the_code_and_reaches_the_agent(client):
    user = _login(client, "9000000301")
    reply = _ask(client, user, "My phone was stolen on a train. Which section applies?", "2024-03-12").json()
    trace = " ".join((reply.get("meta") or {}).get("trace") or [])
    if (reply.get("meta") or {}).get("mode") == "agent":
        assert "incident date 2024-03-12" in trace
    _ask(client, user, "How do I file an FIR?", date.today().isoformat())
    _ask(client, user, "Can my society stop me keeping a pet?")
    matters = client.get("/api/chat/matters", headers=user).json()["matters"]
    assert [m["code"] for m in matters] == [None, "new", "old"]
    assert matters[2]["incident_date"] == "2024-03-12"
    assert all(m["status"] for m in matters)


def test_clocks_start_on_the_incident_date(client):
    user = _login(client, "9000000302")
    ten_days_ago = (date.today() - timedelta(days=10)).isoformat()
    _ask(client, user, "My tenant's rent cheque bounced. What can I do?", ten_days_ago)
    _ask(client, user, "An online seller sent me a fake product")
    clocks = client.get("/api/chat/matters", headers=user).json()["clocks"]
    assert clocks[0]["title"].startswith("Send the demand notice")
    assert clocks[0]["days_left"] == 20
    assert clocks[1]["due"] is None and "Consumer Protection Act 2019 s.69" in clocks[1]["rule"]


def test_matters_are_private_and_dates_cannot_be_in_the_future(client):
    owner = _login(client, "9000000303")
    other = _login(client, "9000000304")
    _ask(client, owner, "My landlord kept my deposit", "2026-01-05")
    assert client.get("/api/chat/matters", headers=other).json()["matters"] == []
    assert client.get("/api/chat/matters").status_code == 401
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert _ask(client, owner, "How do I file an FIR?", tomorrow).status_code == 422


def test_deadline_rules():
    assert add_years(date(2024, 2, 29), 2) == date(2026, 2, 28)
    assert match("RTI reply never came").title == "File the first RTI appeal"
    assert match("What is theft?") is None
