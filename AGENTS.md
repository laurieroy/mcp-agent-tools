# mcp-agent-tools

MCP-augmented ops assistant: FastMCP server exposing three sandboxed tools
(read-only SQLite query runner, live weather REST client, AST math evaluator)
→ MCP host client over stdio → multi-turn LLM function-calling loop →
Streamlit operator console. Work one milestone at a time: finish the code,
give the user the exact test and commit commands, then stop and wait.

## References (read on demand, don't duplicate here)
- `docs/week7_assignment.md` — full spec; tool requirements §4 Step 2, audit
  checklist §4 Step 3, UI §4 Step 4, test names/criteria §4 Step 5,
  submission template §6, README §7
- `docs/week7_work_plan.md` — per-milestone checklists, Definition of Done,
  demo script, rubric cross-check

## Stack
Python 3.11, uv, `mcp[cli]`/FastMCP, httpx, pydantic, aiosqlite,
python-dotenv, Streamlit, pytest, pytest-asyncio. LLM SDK per
`DECISIONS.md` (locked at M0).

## Commands
- Install: `uv sync`
- Test: `uv run pytest -v`
- MCP server standalone: `uv run python -m src.server.mcp_server`
- UI: `uv run streamlit run src/app.py`

## Security invariants (the durable contract)
- SQL tool `query_database`: connect via `file:...?mode=ro` URI; accept
  exactly one `SELECT` statement — reject `;`-separated stacked queries,
  SQL comments, and any DDL/DML keyword.
- Math tool `calculate_expression`: `ast.parse` + node whitelist
  (`Expression`, `BinOp`, `UnaryOp`, numeric `Constant`, `Call` to an
  allowlisted math-function set). Never `eval()`, `exec()`, or `numexpr`.
- Weather tool `get_current_weather`: async httpx with an explicit timeout;
  normalize the API payload before returning it.
- Agent loop: hard `max_turns` bound (default 5); tool exceptions are
  returned to the model as formatted error strings — the loop never
  crashes on a tool failure.
- Tool error strings never contain stack traces or filesystem paths.

## Rules
- NEVER read, edit, print, or search `.env` files (or any real secrets),
  including via shell commands like `cat`, `grep`, `head`. Only
  `.env.example` may be edited, with placeholder values.
- Secrets come from environment variables (`.env` locally via
  `python-dotenv`). Never hard-code keys or model names — model via env var.
- Tests are deterministic and need no API keys or network: mock the LLM
  client and HTTP calls.
- Mock fidelity: fixtures must mirror real API response shapes (captured
  from actual calls at M0 into `tests/fixtures/`), not idealized ones.
  Idealized mocks let real response-format bugs escape until runtime.
- Keep solutions simple and minimal. Don't add features or fixes beyond
  the current milestone.

## Working style
- Manual mode always: check with the user before doing anything. Do only
  what is specifically asked, nothing extra.
- Be concise. Short answers; no long explanations, recaps, or unrequested
  suggestions.
- No hallucination: if unsure, say so or ask. Never invent APIs, flags,
  file contents, or results.
- Never run git commands or uv/test commands (`uv init`, `uv sync`,
  `uv add`, `uv run pytest`, etc.). The user runs them. Give the exact
  command to run instead, then wait for the user to paste the output.
- Before telling the user to commit, recheck every file that will be
  committed for sensitive information (keys, tokens, passwords, emails,
  personal data, local paths) and report what was found, or that nothing
  was found.
- Milestone mechanics (branches, command cards, DoD gates) live in
  `docs/week7_work_plan.md`.

## Decisions
- `DECISIONS.md` is the user's decision log. The user makes every design
  call; the agent proposes options but never decides for them. Whenever a
  direction or tradeoff is discussed, ask the user if they'd like to log
  it — on yes, append one short line (decision + why, in the user's
  voice). Don't restate decisions here; this file stays stable.

## Prompt log
- `ai_prompt_log.md` is a graded deliverable: verbatim prompt, raw output,
  audit findings, fixes — append one entry per milestone (pre-authorized
  exception to manual mode). "Model used" = self-reported (e.g.
  `devin/swe-2-high`).
- Log every real bug as it happens (failing test, wrong output, bad AI
  suggestion): show the bug, the evidence, the root cause, and the commit
  where it was fixed. Feeds the audit and the video segment.
- Include an "escaped defects" line per milestone: bugs found after that
  milestone's DoD was met.
- Log only what actually happened — "none found" is a valid entry.
