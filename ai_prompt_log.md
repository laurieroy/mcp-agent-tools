# AI Prompt Log

## Baseline scaffold (M0–M2) — 2026-11-24

- **Model used:** Devin (Adaptive)
- **Prompt (operative request):** "Build out this folder structure please" — the spec tree from `docs/week7_assignment.md` §4 Step 1, adapted to my M0 decisions (see `DECISIONS.md`): Anthropic Claude via `AGENT_MODEL`, stdio transport, Open-Meteo, spec `src/` layout with uv boilerplate dropped, Python 3.13, `max_turns=5`.
- **Raw output (unmodified baseline, committed as generated):**
  - `src/server/mcp_server.py` — `MCPServer` over stdio exposing `query_database`, `get_current_weather`, `calculate_expression`
  - `src/server/tools/{sql_tool,weather_tool,math_tool}.py` — read-only SQLite (`mode=ro` URI, single-SELECT validation), async Open-Meteo client, AST-whitelist math evaluator (no `eval`/`exec`)
  - `src/client/{mcp_client,agent_loop}.py` — stdio `MCPClient` with dynamic `list_tools()` discovery → Anthropic tool schema; multi-turn `run_agent` with `max_turns` bound and tool errors fed back to the model
  - `src/app.py` — Streamlit console with tool inspector, tool-call trace, adversarial workbench
  - `scripts/seed_db.py` → `data/enterprise_ops.db` (customers/orders/products/inventory, incl. Seattle SKU-90210 and order #4492)
  - `tests/` — Tests 1–7 per §4 Step 5, deterministic (mocked httpx/LLM)
- **Spec deviation noted:** installed `mcp` is 2.3.0 — `mcp.server.fastmcp.FastMCP` was renamed to `mcp.server.mcpserver.MCPServer`; the spec's FastMCP import does not exist in this version.
- **Audit findings:** none yet — cross-model audit is M3.
- **Bugs logged:** none found.
- **Escaped defects:** none yet.
