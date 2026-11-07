"""Postgres checkpoints: an answer held for advocate review survives a restart (docs/MEMORY.md).

Uses `NYA_TEST_DATABASE_URL` (default: the docker-compose `nya_test` database); skipped when it is down.
"""

import os
import uuid

import pytest

from app.agents import runner as runner_mod
from app.agents.graph import Tools
from app.agents.runner import AgentRunner, postgres_checkpointer
from tests.agents.test_graph import search, sql

URL = os.environ.get("NYA_TEST_DATABASE_URL", "postgresql+psycopg://nya:nya@localhost:5433/nya_test")


@pytest.fixture
def saver():
    try:
        return postgres_checkpointer(URL)
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        pytest.skip("Postgres not reachable")


def test_review_resumes_after_a_restart(saver):
    thread = f"pg-{uuid.uuid4().hex}"
    q = "My brother was arrested yesterday under BNS 303. What does the section say?"
    paused = AgentRunner(Tools(search=search, sql=sql), saver).run(q, thread)
    assert paused.answer.status == "pending_review"

    # A new runner with a new connection pool stands in for a restarted API process.
    restarted = AgentRunner(Tools(search=search, sql=sql), postgres_checkpointer(URL))
    done = restarted.resume(thread, {"decision": "approved"})
    assert done.answer.status == "reviewed"


def test_falls_back_to_sqlite_when_postgres_is_down(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from langgraph.checkpoint.sqlite import SqliteSaver

    down = SimpleNamespace(
        CHECKPOINT_DATABASE_URL="postgresql://nobody@localhost:1/none", CHECKPOINT_DB=str(tmp_path / "c.db")
    )
    monkeypatch.setattr(runner_mod, "get_settings", lambda: down)
    assert isinstance(runner_mod.default_checkpointer(), SqliteSaver)
