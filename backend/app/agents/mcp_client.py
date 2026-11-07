"""The graph's law tools through MCP, behind `TOOLS_VIA_MCP` (off by default, so latency is unchanged).

One MCP session stays open on a background event loop; the graph's synchronous nodes call it with
`search()` and `sql()`, the same shapes as the direct tools in `graph.default_tools()`. The session is
stdio to `python -m app.agents.mcp_server` by default, or streamable HTTP when `MCP_SERVER_URL` is set.
"""

import asyncio
import json
import os
import sys
import threading
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

from mcp import ClientSession

from app.rag.retrieve import Evidence

BACKEND_DIR = Path(__file__).resolve().parents[2]
Connect = Callable[[], AbstractAsyncContextManager[ClientSession]]


@asynccontextmanager
async def stdio_session():
    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable, args=["-m", "app.agents.mcp_server"], cwd=str(BACKEND_DIR), env=dict(os.environ)
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        yield session


def http_session(url: str) -> Connect:
    @asynccontextmanager
    async def connect():
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(url) as (read, write, _), ClientSession(read, write) as session:
            await session.initialize()
            yield session

    return connect


def result_value(result: Any) -> Any:
    """A tool result as plain data: structured content when present, else the JSON text."""
    if getattr(result, "isError", False):
        raise RuntimeError(" ".join(getattr(c, "text", "") for c in result.content) or "MCP tool error")
    sc = getattr(result, "structuredContent", None)
    if sc is not None:
        return sc["result"] if set(sc) == {"result"} else sc
    text = "".join(getattr(c, "text", "") for c in result.content)
    return json.loads(text) if text else None


class McpLawClient:
    def __init__(self, connect: Connect | None = None, timeout: float = 60):
        self._connect = connect or stdio_session
        self._timeout = timeout
        self._session: ClientSession | None = None
        self._stop: asyncio.Event | None = None
        self._ready = threading.Event()
        self._error: BaseException | None = None
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name="mcp-law-client", daemon=True)
        self._thread.start()
        self._main = asyncio.run_coroutine_threadsafe(self._open(), self._loop)
        if not self._ready.wait(timeout):
            raise TimeoutError("MCP server did not start")
        if self._error:
            raise self._error

    async def _open(self) -> None:
        self._stop = asyncio.Event()
        try:
            async with self._connect() as session:
                self._session = session
                self._ready.set()
                await self._stop.wait()
        except BaseException as e:  # pylint: disable=broad-exception-caught  # reported to the caller
            self._error = e
            self._ready.set()

    def call(self, tool: str, args: dict) -> Any:
        if self._session is None:
            raise RuntimeError("MCP session is closed")
        fut = asyncio.run_coroutine_threadsafe(self._session.call_tool(tool, args), self._loop)
        return result_value(fut.result(self._timeout))

    def list_tools(self) -> list[str]:
        fut = asyncio.run_coroutine_threadsafe(self._session.list_tools(), self._loop)
        return sorted(t.name for t in fut.result(self._timeout).tools)

    # ---- the graph's Tools shapes ----

    def search(self, question: str, as_of: date, acts: list[str]) -> tuple[list[Evidence], bool]:
        out = self.call("law_search", {"question": question, "as_of": as_of.isoformat(), "acts": acts})
        return [Evidence(**e) for e in out["evidence"]], bool(out["library_up"])

    def sql(self, template: str, params: dict) -> Any:
        out = self.call("sql_lookup", {"template": template, "params": params})
        if "error" in out:
            raise ValueError(out["error"])
        return out["rows"]

    def close(self) -> None:
        if self._stop is not None:
            self._loop.call_soon_threadsafe(self._stop.set)
        try:
            self._main.result(10)
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
