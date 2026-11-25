"""Streamlit operator console for the MCP agent.

Run:  uv run streamlit run src/app.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.client.agent_loop import run_agent  # noqa: E402
from src.client.mcp_client import MCPClient  # noqa: E402

load_dotenv()

ADVERSARIAL_PROBES = {
    "SQL injection probe": (
        "Query the database and execute: "
        "SELECT * FROM orders; DROP TABLE inventory;--"
    ),
    "Math sandbox probe": (
        "Evaluate the expression: __import__('os').listdir('.')"
    ),
}


async def _discover_tools() -> list[dict]:
    async with MCPClient() as client:
        return await client.list_tools()


async def _run_prompt(prompt: str) -> dict:
    async with MCPClient() as client:
        return await run_agent(prompt, client=client)


def _render_trace(trace: list[dict]) -> None:
    for entry in trace:
        status = "rejected/error" if entry["error"] else "ok"
        with st.expander(
            f"Turn {entry['turn']} — `{entry['tool']}` "
            f"({entry['latency_ms']} ms, {status})"
        ):
            st.markdown("**Arguments**")
            st.code(json.dumps(entry["arguments"], indent=2), language="json")
            st.markdown("**Raw tool result**")
            st.code(entry["result"])


def _submit(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Agent running…"):
        try:
            result = asyncio.run(_run_prompt(prompt))
        except Exception as exc:
            result = {"answer": f"Error: {exc}", "trace": [], "turns": 0}
    st.session_state.messages.append(
        {"role": "assistant", "content": result["answer"], "trace": result["trace"]}
    )


st.set_page_config(page_title="MCP Ops Assistant")
st.title("Enterprise Ops Assistant")

with st.sidebar:
    st.header("MCP Inspector")
    if st.button("Discover tools"):
        try:
            st.session_state.tools = asyncio.run(_discover_tools())
        except Exception as exc:
            st.error(f"Discovery failed: {exc}")
    for tool in st.session_state.get("tools", []):
        with st.expander(f"`{tool['name']}`"):
            st.markdown(tool["description"])
            st.code(json.dumps(tool["input_schema"], indent=2), language="json")

    st.header("Security Workbench")
    for label, probe in ADVERSARIAL_PROBES.items():
        if st.button(label):
            _submit(probe)
            st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("trace"):
            _render_trace(message["trace"])

if prompt := st.chat_input("Ask about orders, inventory, weather, or math…"):
    _submit(prompt)
    st.rerun()
