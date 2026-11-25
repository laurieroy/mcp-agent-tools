# Decisions

**LLM:** Anthropic Claude, model name via `AGENT_MODEL` env var (never hard-coded). I already have an Anthropic key; the `openai` dep stays until the M7 cleanup pass.

**MCP transport:** stdio — the client spawns the server as a child process; no ports or extra process management for a local assignment.

**Layout:** spec `src/` layout (`src/server`, `src/client`, `src/app.py`). Dropped the `uv init` boilerplate (`src/mcp_agent_tools`, `[project.scripts]`, `build-system`); `package = false` since this app is never pip-installed.

**Python:** staying on 3.13 (venv already synced; nothing in the stack requires 3.11 specifically).

**Weather API:** Open-Meteo — real REST API, geocoding + forecast, no API key needed.
- Also a new-to-me API learning experience

**Agent loop bound:** `max_turns = 5` (spec default; enough for the 3-tool Seattle demo).

