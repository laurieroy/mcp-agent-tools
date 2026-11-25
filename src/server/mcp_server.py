"""MCP server exposing the three sandboxed ops tools over stdio.

Run standalone:  uv run python -m src.server.mcp_server

Note: installed ``mcp`` is 2.x, where ``FastMCP`` was renamed to
``MCPServer`` (``mcp.server.mcpserver``).
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .tools import math_tool, sql_tool, weather_tool

mcp = MCPServer("enterprise-ops")


@mcp.tool()
async def query_database(sql_query: str) -> str:
    """Run a read-only SQL SELECT query against the enterprise ops SQLite
    database (customers, orders, products, inventory).

    Only a single SELECT statement is allowed: stacked queries, comments,
    and all DDL/DML keywords are rejected, and the connection itself is
    opened read-only.
    """
    return await sql_tool.query_database(sql_query)


@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Fetch live current weather conditions for a city via Open-Meteo:
    temperature, conditions, precipitation, wind speed, and humidity."""
    return await weather_tool.get_current_weather(city)


@mcp.tool()
def calculate_expression(expression: str) -> str:
    """Evaluate an arithmetic expression deterministically.

    Supports + - * / ** % //, parentheses, abs/round/min/max, whitelisted
    math.* functions, and the constants pi/e/tau. Anything else is
    rejected by the AST whitelist — never use for non-numeric input.
    """
    return math_tool.calculate_expression(expression)


if __name__ == "__main__":
    mcp.run()  # stdio transport
