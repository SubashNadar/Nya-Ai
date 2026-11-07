# ADR 0004: MCP for law data only, read-only, no free text-to-SQL

- **Date:** 2026-11-01
- **Status:** Accepted

## Context

The course asks for tool integration over MCP. Giving a model tools is also the main
prompt-injection risk: a tool that can read user records lets an injected prompt read another user's
data.

## Decision

Six read-only MCP tools over law data only: `law_search`, `get_section`, `search_judgments`,
`map_ipc_to_bns`, `acts_in_force` and `sql_lookup`. SQL goes through fixed, parameterised templates;
the model picks a template and never writes SQL. Users, advocates, bookings, briefs and payments are
reached only by FastAPI services under login. Built as a FastMCP server (stdio and streamable HTTP).
The graph calls the functions directly by default and can route through MCP with
`TOOLS_VIA_MCP=true`.

## Consequences

An injected prompt can at most read public law. The SQL agent cannot express a query outside the
templates. `mcp` is pinned to 1.x until the 2.x API settles.

## References

`backend/app/agents/mcp_server.py`, `mcp_client.py`, `app/rag/sql_queries.py`
