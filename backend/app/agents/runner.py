"""Runs the R1 graph for one turn: checkpointing, Langfuse tracing and scores, streaming, resume.

Checkpoints (the graph's short-term memory, docs/MEMORY.md) go to Postgres when
`CHECKPOINT_DATABASE_URL` is set, else to SQLite (`CHECKPOINT_DB`), so an answer held for advocate
review survives a restart. If Postgres is down at start-up the runner falls back to SQLite. Tests pass
an in-memory checkpointer.
"""

import hashlib
import logging
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from langgraph.types import Command

from app.agents.graph import Tools, build_answer, build_graph, default_tools, pending_answer
from app.agents.state import Answer
from app.core.config import get_settings
from app.core.observability import langfuse

logger = logging.getLogger(__name__)


# Pydantic models the graph keeps in its state; the checkpointer may load only these.
STATE_TYPES = [
    ("app.rag.retrieve", "Evidence"),
    *(("app.agents.state", name) for name in ("Answer", "Citation", "Critique", "Draft", "SqlResult")),
]


def serializer():
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    return JsonPlusSerializer(allowed_msgpack_modules=STATE_TYPES)


def memory_checkpointer():
    from langgraph.checkpoint.memory import InMemorySaver

    return InMemorySaver(serde=serializer())


def sqlite_checkpointer():
    from langgraph.checkpoint.sqlite import SqliteSaver

    conn = sqlite3.connect(get_settings().CHECKPOINT_DB, check_same_thread=False)
    return SqliteSaver(conn, serde=serializer())


def postgres_checkpointer(url: str):
    """A PostgresSaver on a small connection pool; creates its tables on first use."""
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    pool = ConnectionPool(
        url,
        min_size=1,
        max_size=5,
        open=True,
        timeout=5,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    saver = PostgresSaver(pool, serde=serializer())
    saver.setup()
    return saver


def default_checkpointer():
    url = get_settings().CHECKPOINT_DATABASE_URL
    if url:
        try:
            return postgres_checkpointer(url)
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught  # SQLite keeps chat working
            logger.warning("Postgres checkpointer unavailable, falling back to SQLite", exc_info=True)
    return sqlite_checkpointer()


@dataclass
class TurnResult:
    answer: Answer
    thread_id: str
    trace_id: str | None = None
    review: dict | None = None  # the interrupt payload when the answer waits for an advocate
    evidence: list = field(default_factory=list)  # retrieved sections, for the eval answer run


def user_hash(user_id: str | None) -> str | None:
    """What Langfuse sees instead of a user id (never the phone number)."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16] if user_id else None


class AgentRunner:
    def __init__(self, tools: Tools | None = None, checkpointer=None):
        if checkpointer is None:
            checkpointer = default_checkpointer()
        self.graph = build_graph(tools or default_tools(), checkpointer)

    # ---- config and observability ----

    def _config(self, thread_id: str, conversation_id: str | None, user_id: str | None) -> tuple[dict, Any]:
        config: dict = {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}
        handler = None
        if langfuse() is not None:
            try:
                from langfuse.langchain import CallbackHandler

                handler = CallbackHandler()
                config["callbacks"] = [handler]
                config["metadata"] = {
                    "langfuse_session_id": conversation_id or thread_id,
                    "langfuse_user_id": user_hash(user_id),
                    "langfuse_tags": ["nya-agent", "r1"],
                }
            except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught  # tracing is optional
                logger.exception("Langfuse callback unavailable")
        return config, handler

    @staticmethod
    def _scores(handler: Any, answer: Answer) -> str | None:
        trace_id = getattr(handler, "last_trace_id", None) if handler else None
        client = langfuse()
        if not (trace_id and client):
            return trace_id
        try:
            if answer.confidence is not None:
                client.create_score(trace_id=trace_id, name="confidence", value=answer.confidence)
            client.create_score(trace_id=trace_id, name="route", value=answer.route, data_type="CATEGORICAL")
            client.create_score(trace_id=trace_id, name="escalation", value=answer.escalation, data_type="CATEGORICAL")
            if answer.status in ("answered", "reviewed"):
                client.create_score(
                    trace_id=trace_id, name="citations_valid", value=1 if answer.citations else 0, data_type="BOOLEAN"
                )
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            logger.exception("Langfuse scores not sent")
        return trace_id

    def _result(self, config: dict, handler: Any, thread_id: str) -> TurnResult:
        snapshot = self.graph.get_state(config)
        values = snapshot.values
        pending = [i.value for task in snapshot.tasks for i in task.interrupts]
        if pending:
            answer = pending_answer(values)
            answer.trace = values.get("trace", [])
            return TurnResult(
                answer, thread_id, self._scores(handler, answer), review=pending[0], evidence=values.get("evidence", [])
            )
        answer = values.get("answer") or build_answer(values)
        answer.trace = values.get("trace", [])
        return TurnResult(answer, thread_id, self._scores(handler, answer), evidence=values.get("evidence", []))

    @staticmethod
    def _input(question: str, history: list[dict] | None, incident_date: str | None = None) -> dict:
        return {"question": question, "history": history or [], "incident_date": incident_date}

    # ---- entry points ----

    def run(
        self,
        question: str,
        thread_id: str,
        conversation_id: str | None = None,
        user_id: str | None = None,
        history: list[dict] | None = None,
        incident_date: str | None = None,
    ) -> TurnResult:
        config, handler = self._config(thread_id, conversation_id, user_id)
        self.graph.invoke(self._input(question, history, incident_date), config)
        return self._result(config, handler, thread_id)

    def stream(
        self,
        question: str,
        thread_id: str,
        conversation_id: str | None = None,
        user_id: str | None = None,
        history: list[dict] | None = None,
    ) -> Iterator[dict]:
        """One event per finished node ({"event": "node", ...}), then {"event": "answer", ...}."""
        config, handler = self._config(thread_id, conversation_id, user_id)
        for update in self.graph.stream(self._input(question, history), config, stream_mode="updates"):
            for node, values in update.items():
                if node == "__interrupt__":
                    continue
                lines = (values or {}).get("trace") or []
                yield {"event": "node", "node": node, "line": lines[-1] if lines else node}
        result = self._result(config, handler, thread_id)
        yield {"event": "answer", "result": result}

    def resume(self, thread_id: str, decision: dict) -> TurnResult:
        """Resume a run paused for advocate review with {"decision": approved|edited|rejected, ...}."""
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = self.graph.get_state(config)
        if not any(task.interrupts for task in snapshot.tasks):
            raise LookupError(f"no answer is waiting for review on {thread_id}")
        self.graph.invoke(Command(resume=decision), config)
        return self._result(config, None, thread_id)


@lru_cache
def get_runner() -> AgentRunner:
    return AgentRunner()
