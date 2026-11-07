"""Nya-AI law tools as an MCP server: read-only, law data only (docs/DECISIONS.md).

Six tools, each a thin wrapper over the law library code the graph already uses:

- `law_search`       hybrid search of the bare acts in force on a date
- `get_section`      one section's text by act and number
- `search_judgments` placeholder until judgments are ingested; says so instead of guessing
- `map_ipc_to_bns`   the BNS section(s) that replaced an IPC section
- `acts_in_force`    which criminal codes apply on a date
- `sql_lookup`       one of the fixed, parameterised SQL templates; no free text-to-SQL

No tool reaches users, bookings, briefs or payments. Run it with `uv run nya-agent mcp` (stdio, for
Claude Desktop or the MCP Inspector) or `uv run nya-agent mcp --http` (streamable HTTP on :8765/mcp).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.rag.acts import ACTS
from app.rag.acts import acts_in_force as _acts_in_force

INSTRUCTIONS = (
    "Read-only tools over Indian bare acts (BNS, BNSS, BSA, IPC). Pass the date the law is needed for: "
    "the IPC applies before 1 July 2024, the BNS, BNSS and BSA from then. Results are public legal "
    "information with section citations, not legal advice."
)
JUDGMENTS_NOTE = "Judgments are not loaded yet: the library holds the bare acts only (BNS, BNSS, BSA, IPC)."


@dataclass
class LawBackend:
    """What the tools call. The default reads the real library; tests pass fakes."""

    search: Callable[[str, date, list[str]], tuple[list[Any], bool]]
    section: Callable[[str, str], dict | None]
    sql: Callable[[str, dict], Any]


def default_backend() -> LawBackend:
    from app.agents.graph import law_engine, library_search
    from app.rag import sql_queries, tables

    return LawBackend(
        search=library_search,
        section=lambda act, num: tables.get_section(law_engine(), act, num),
        sql=lambda template, params: sql_queries.run(law_engine(), template, **params),
    )


def _day(value: str | None) -> date:
    return date.fromisoformat(value) if value else date.today()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    return value


def sql_templates() -> list[str]:
    from app.rag.sql_queries import TEMPLATES

    return sorted(TEMPLATES)


def build_server(backend: LawBackend | None = None, **settings: Any) -> FastMCP:
    """The MCP server with the six law tools bound to `backend` (the real library by default)."""
    server = FastMCP("nya-ai-law", instructions=INSTRUCTIONS, **settings)
    lazy: dict[str, LawBackend] = {}

    def law() -> LawBackend:
        if "b" not in lazy:
            lazy["b"] = backend or default_backend()
        return lazy["b"]

    @server.tool()
    def law_search(question: str, as_of: str | None = None, acts: list[str] | None = None) -> dict:
        """Search the bare acts in force on `as_of` (YYYY-MM-DD, default today); optionally limit to `acts`.

        Returns the matching sections with act, section, heading, text, page and score, and whether the
        library was reachable."""
        day = _day(as_of)
        scope = _acts_in_force(day, acts) or (acts or [])
        evidence, up = law().search(question, day, scope)
        return {"as_of": day.isoformat(), "acts": scope, "library_up": up, "evidence": _jsonable(evidence)}

    @server.tool()
    def get_section(act: str, section: str) -> dict:
        """The text of one section, e.g. act="BNS", section="303"."""
        act = act.upper()
        if act not in ACTS:
            return {"error": f"unknown act {act!r}; known: {', '.join(ACTS)}"}
        row = law().section(act, section)
        return _jsonable(row) if row else {"error": f"{act} section {section} not found"}

    @server.tool()
    def search_judgments(query: str, court: str | None = None) -> dict:
        """Search court judgments. Not available yet: returns an empty list and a note."""
        return {"query": query, "court": court, "results": [], "note": JUDGMENTS_NOTE}

    @server.tool()
    def map_ipc_to_bns(ipc_section: str) -> dict:
        """The BNS section(s) that replaced an IPC section, e.g. "420" -> BNS 318(4)."""
        rows = law().sql("replacement", {"old_act": "IPC", "old_section": ipc_section})
        return {"ipc_section": ipc_section, "bns": _jsonable(rows)}

    @server.tool()
    def acts_in_force(on: str | None = None) -> dict:
        """The criminal codes that apply on a date (YYYY-MM-DD, default today)."""
        day = _day(on)
        return {"on": day.isoformat(), "acts": [{"code": c, "title": ACTS[c].title} for c in _acts_in_force(day)]}

    @server.tool()
    def sql_lookup(template: str, params: dict | None = None) -> dict:
        """Run one fixed SQL template over the law tables. Templates: replacement(old_act, old_section),
        new_offences(act), in_force_from(code), acts_in_force_on(day), repealed_in(year), offence(act, section),
        count_offences(act, bailable), life_or_death(act), section_count(act)."""
        if template not in sql_templates():
            return {"error": f"unknown template {template!r}", "templates": sql_templates()}
        try:
            rows = law().sql(template, params or {})
        except TypeError as e:  # wrong or missing parameters
            return {"error": f"bad parameters for {template}: {e}"}
        return {"template": template, "params": params or {}, "rows": _jsonable(rows)}

    return server


def preload() -> LawBackend:
    """Import the library (numpy, LlamaIndex, the Azure client) before serving.

    On Windows a first import of numpy's C extension inside a tool call can deadlock with the stdio
    reader thread, so everything heavy is imported here, on the main thread, before the transport starts.
    """
    import llama_index.embeddings.azure_openai  # noqa: F401  # pylint: disable=unused-import
    import numpy  # noqa: F401  # pylint: disable=unused-import

    from app.rag import index, retrieve  # noqa: F401  # pylint: disable=unused-import

    return default_backend()


def main(http: bool = False, host: str = "127.0.0.1", port: int = 8765) -> None:
    backend = preload()
    if http:
        build_server(backend, host=host, port=port).run(transport="streamable-http")
    else:
        build_server(backend).run()


if __name__ == "__main__":
    main()
