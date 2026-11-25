"""Multi-turn function-calling loop: Anthropic Claude <-> MCP tools.

The loop is bounded by ``max_turns`` (default 5, override via the
``AGENT_MAX_TURNS`` env var). Tool failures are fed back to the model as
``tool_result`` error blocks instead of crashing the loop.
"""

from __future__ import annotations

import os
import time
from typing import Any

from .mcp_client import MCPClient

_DEFAULT_MAX_TURNS = 5


def _default_llm() -> Any:
    import anthropic  # lazy: tests inject a fake LLM and don't need the SDK

    return anthropic.AsyncAnthropic()


async def run_agent(
    user_prompt: str,
    *,
    client: MCPClient,
    llm: Any = None,
    model: str | None = None,
    max_turns: int | None = None,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """Run the agent loop for one user prompt.

    Returns ``{"answer": str, "trace": list, "turns": int}`` where each
    ``trace`` entry records tool name, arguments, raw result, turn number,
    and latency for the UI inspector panel.
    """
    model = model or os.environ.get("AGENT_MODEL")
    if not model:
        raise RuntimeError("AGENT_MODEL environment variable is not set")
    max_turns = max_turns or int(
        os.environ.get("AGENT_MAX_TURNS", _DEFAULT_MAX_TURNS)
    )
    llm = llm or _default_llm()

    tools = await client.list_tools()
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
    trace: list[dict[str, Any]] = []

    for turn in range(1, max_turns + 1):
        response = await llm.messages.create(
            model=model,
            max_tokens=max_tokens,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [
            block
            for block in response.content
            if getattr(block, "type", None) == "tool_use"
        ]
        if not tool_uses:
            answer = "".join(
                getattr(block, "text", "")
                for block in response.content
                if getattr(block, "type", None) == "text"
            )
            return {"answer": answer or "(empty response)", "trace": trace, "turns": turn}

        tool_results = []
        for call in tool_uses:
            started = time.perf_counter()
            try:
                output = await client.call_tool(call.name, dict(call.input))
                is_error = False
            except Exception as exc:
                output = f"Error: tool '{call.name}' failed: {exc}"
                is_error = True
            trace.append(
                {
                    "turn": turn,
                    "tool": call.name,
                    "arguments": dict(call.input),
                    "result": output,
                    "error": is_error,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                }
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": output,
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return {
        "answer": f"Stopped: reached max_turns={max_turns} without a final answer.",
        "trace": trace,
        "turns": max_turns,
    }
