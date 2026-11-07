"""The MCP law server and the graph's MCP adapter, in memory with a fake library: no Postgres, no Azure."""

import asyncio
from contextlib import asynccontextmanager
from datetime import date

from mcp.shared.memory import create_connected_server_and_client_session

from app.agents.graph import Tools
from app.agents.mcp_client import McpLawClient, result_value
from app.agents.mcp_server import JUDGMENTS_NOTE, LawBackend, build_server
from app.agents.runner import AgentRunner, memory_checkpointer
from tests.agents.test_graph import THEFT, search

SECTIONS = {
    ("BNS", "303"): {"act": "BNS", "section": "303", "heading": "Theft", "text": "303. (1) Whoever...", "page": "88"}
}


def fake_sql(template: str, params: dict):
    if template == "replacement":
        return [["BNS", "318(4)"]] if params["old_section"] == "420" else []
    if template == "section_count":
        return 358
    raise AssertionError(template)


FAKE = LawBackend(search=search, section=lambda act, num: SECTIONS.get((act, num)), sql=fake_sql)
TOOLS = ["acts_in_force", "get_section", "law_search", "map_ipc_to_bns", "search_judgments", "sql_lookup"]


def call(tool: str, args: dict):
    async def go():
        async with create_connected_server_and_client_session(build_server(FAKE)._mcp_server) as session:  # pylint: disable=protected-access
            if tool == "__list__":
                return sorted(t.name for t in (await session.list_tools()).tools)
            return result_value(await session.call_tool(tool, args))

    return asyncio.run(go())


def test_lists_the_six_read_only_tools():
    assert call("__list__", {}) == TOOLS


def test_law_search_uses_the_acts_in_force_on_the_date():
    after = call("law_search", {"question": "theft", "as_of": "2024-08-01"})
    assert after["acts"] == ["BNS", "BNSS", "BSA"]
    assert [(e["act"], e["section"]) for e in after["evidence"]] == [("BNS", "303")]
    before = call("law_search", {"question": "theft", "as_of": "2024-03-12"})
    assert before["acts"] == ["IPC"]
    assert [(e["act"], e["section"]) for e in before["evidence"]] == [("IPC", "378")]


def test_get_section_and_unknown_inputs():
    assert call("get_section", {"act": "bns", "section": "303"})["heading"] == "Theft"
    assert "not found" in call("get_section", {"act": "BNS", "section": "999"})["error"]
    assert "unknown act" in call("get_section", {"act": "CPC", "section": "1"})["error"]


def test_map_acts_judgments_and_sql():
    assert call("map_ipc_to_bns", {"ipc_section": "420"})["bns"] == [["BNS", "318(4)"]]
    assert [a["code"] for a in call("acts_in_force", {"on": "2024-03-12"})["acts"]] == ["IPC"]
    assert call("search_judgments", {"query": "bail"}) == {
        "query": "bail",
        "court": None,
        "results": [],
        "note": JUDGMENTS_NOTE,
    }
    assert call("sql_lookup", {"template": "section_count", "params": {"act": "BNS"}})["rows"] == 358
    bad = call("sql_lookup", {"template": "drop_table", "params": {}})
    assert "unknown template" in bad["error"] and "section_count" in bad["templates"]


def test_graph_answers_through_the_mcp_adapter():
    @asynccontextmanager
    async def connect():
        async with create_connected_server_and_client_session(build_server(FAKE)._mcp_server) as session:  # pylint: disable=protected-access
            yield session

    client = McpLawClient(connect)
    try:
        assert client.list_tools() == TOOLS
        evidence, up = client.search("What does BNS section 303 say?", date(2024, 8, 1), ["BNS"])
        assert up and evidence == [THEFT]
        runner = AgentRunner(Tools(search=client.search, sql=client.sql), memory_checkpointer())
        a = runner.run("Which BNS section replaced IPC 420?", "mcp-1").answer
        assert a.route == "sql" and "BNS 318(4)" in a.text
        a = runner.run("What does BNS section 303 say?", "mcp-2").answer
        assert [(c.act, c.section) for c in a.citations] == [("BNS", "303")]
    finally:
        client.close()
