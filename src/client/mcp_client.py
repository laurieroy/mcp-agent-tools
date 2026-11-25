"""MCP host client: spawns the server over stdio, discovery + dispatch."""

from __future__ import annotations

import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_REPO_ROOT = Path(__file__).resolve().parents[2]


class MCPClient:
    """Async context manager wrapping an MCP ``ClientSession`` on stdio.

    Spawns ``python -m src.server.mcp_server`` as a child process whose
    lifetime is bound to this client.
    """

    def __init__(self, server_module: str = "src.server.mcp_server") -> None:
        self._params = StdioServerParameters(
            command=sys.executable,
            args=["-m", server_module],
            cwd=str(_REPO_ROOT),
        )
        self._exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None

    async def __aenter__(self) -> "MCPClient":
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(self._params)
        )
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._exit_stack.aclose()

    async def list_tools(self) -> list[dict[str, Any]]:
        """Discover tools and convert MCP schemas to Anthropic tool format."""
        assert self.session is not None, "client not connected"
        result = await self.session.list_tools()
        tools = []
        for tool in result.tools:
            input_schema = getattr(tool, "inputSchema", None) or getattr(
                tool, "input_schema", {}
            )
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": input_schema,
                }
            )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Invoke an MCP tool and return its text content."""
        assert self.session is not None, "client not connected"
        result = await self.session.call_tool(name, arguments)
        parts = [getattr(block, "text", "") for block in result.content]
        text = "\n".join(part for part in parts if part)
        return text or "(empty tool result)"
