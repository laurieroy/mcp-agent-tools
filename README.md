# mcp-agent-tools

Enterprise ops assistant built on the Model Context Protocol: an MCP server exposing three sandboxed tools (read-only SQLite queries, live Open-Meteo weather, AST-based math evaluator), an MCP host client over stdio, a multi-turn Anthropic function-calling loop, and a Streamlit operator console.

## Run locally

```bash
# Clone the repository
git clone https://github.com/laurieroy/mcp-agent-tools.git
cd mcp-agent-tools

# install dependencies (Python 3.13)
uv sync

# configure secrets
cp .env.example .env   # then add your ANTHROPIC_API_KEY and set AGENT_MODEL

# (re)generate the sample SQLite dataset
uv run python scripts/seed_db.py

# run the MCP server standalone (stdio)
uv run python -m src.server.mcp_server

# launch the web UI
uv run streamlit run src/app.py

# run the test suite (no keys or network needed)
uv run pytest -v
```

## Sample use

In the web UI, submit a multi-part prompt that triggers all three tools:

> Check if our inventory in Seattle has enough stock of SKU-90210 to fulfill
> order #4492, verify if rainfall there will delay ground dispatch today, and
> calculate the total shipping insurance cost at 3.5% of the order value.

The agent looks up the order and Seattle inventory via `query_database`,
checks live conditions via `get_current_weather`, computes the insurance via
`calculate_expression`, then synthesizes a grounded summary. The sidebar's
MCP Inspector shows discovered tool schemas; each tool call appears as an
expandable timeline entry with arguments, raw result, and latency.

## Tech stack

| Layer | Tech |
|---|---|
| Language | Python 3.13, managed by `uv` |
| Protocol | `mcp[cli]` (FastMCP server), stdio transport |
| LLM | Anthropic Claude via `anthropic` SDK; model name from `AGENT_MODEL` |
| Tools | SQLite via `aiosqlite` (read-only URI), Open-Meteo REST via `httpx`, AST-whitelist math evaluator |
| Validation | `pydantic` |
| UI | Streamlit operator console |
| Config | `python-dotenv` (`.env`, never committed) |
| Tests | `pytest` + `pytest-asyncio` (deterministic — no keys, no network) |
