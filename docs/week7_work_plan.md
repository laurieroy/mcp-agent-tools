# Work Plan: MCP Tool-Augmented Agent

Companion to `week7_assignment.md`. Built with AI agents, gated by human review.

**How to use this file:** work top to bottom. Tick a checkbox only when its
*Definition of Done* is met and you have run the tests yourself. Commit after
every completed milestone.

---

## Working Rules (apply to every milestone)

1. **One agent task per milestone.** Never ask for the whole system at once.
2. **Spec lives in the repo.** Keep `week7_assignment.md` and `AGENTS.md` at hand.
3. **Tests first.** Agent writes tests, confirm they fail, then implement until green.
4. **You are the gate.** Run `pytest -v` yourself and skim the diff before moving on.
5. **Root cause before fix.** Before the agent touches code for a bug, it
   states the symptom (what you observe) and the root cause (what's actually
   wrong, not the symptom) — one line each. This is the learning step;
   don't skip it.
6. **Every real bug gets logged.** `ai_prompt_log.md`: the bug, the evidence,
   the one-line root cause, and the commit where it was fixed.
7. **Real input before done.** Any milestone that ships a failure/retry/tool-call
   path isn't done until that path has run once against a *real*, non-mocked
   input. Mocks verified week 4's logic but let two real response-format bugs
   escape to the UI — don't repeat it.
8. **Commit after each green milestone** with a message saying what changed and why.

### Milestone mechanics

- **Branch per milestone,** named `mN-<one word>`: `m1-data`, `m2-baseline`,
  `m3-audit`, `m4-hardening`, `m5-ui`, `m6-docker`, `m7-submission` (no branch
  for M0 — it stays on main). Agent hands you `git switch -c mN-<word>` as the
  FIRST step, before any code changes.
- **Command card at milestone end** — the agent closes with one numbered block:
  test command → QA command → commit command → merge command. Run them in order,
  paste back failures.
- **QA gate before merge:** `uv run pytest -v` green (you run it), plus a browser
  QA pass against the running app once the UI exists (M5 onward).
- **Post-milestone checklist:**
  - [ ] Tests pass when I run them
  - [ ] No `eval(`/`exec(`/`numexpr` outside a test that proves it's blocked
        (`grep -rn "eval(\|exec(\|numexpr" src/` returns nothing)
  - [ ] No secrets in the diff
  - [ ] Real-input run done for any new failure path
  - [ ] Prompt-log entry written (bugs shown with fixes, or "none found")
  - [ ] Committed with a clear message

---

## Progress Tracker

| # | Milestone | Effort | Status |
|---|---|---|---|
| M0 | Setup and decisions | ~5% | ☐ — repo initialized; decisions + housekeeping remain |
| M1 | Seed data + math evaluator | ~10% | ☐ |
| M2 | Baseline AI draft (captured untouched) | ~10% | ☐ |
| M3 | Cross-model security audit | ~15% | ☐ |
| M4 | Hardening + Tests 1–7 | ~25% | ☐ |
| M5 | Web UI | ~15% | ☐ |
| M6 | Packaging (Docker) | ~5% | ☐ |
| M7 | README, video, submission | ~15% | ☐ |

---

## M0: Setup and Decisions

**Goal:** the half-done setup finished and the key decisions locked in writing.

**Already done:** `uv init`, `pyproject.toml` with the §4 Step 1 dependency set,
`.venv`, `uv.lock`, initial commit.

**Remaining housekeeping**
- [x] `.gitignore`: add `.env` (currently missing — would leak a key on first
      commit). Keep `.env.example` committable.
- [x] `.env.example` with placeholders per the provider decision below
- [x] `ai_prompt_log.md`, `DECISIONS.md`, `data/`, `tests/fixtures/` created
- [x] Reconcile `src/` layout: `uv` created `src/mcp_agent_tools/__init__.py`;
      the spec wants `src/server/`, `src/client/`, `src/app.py`. Decide: adopt
      the spec layout (drop the boilerplate package + `[project.scripts]`) or
      keep a package name — log it either way.
- [x] Python version: spec says pin 3.11; repo is currently `>=3.13`. Decide and log — staying on 3.13 is a defensible call but should be deliberate.

**Decisions to make first** (log each in `DECISIONS.md`, your voice)
- [x] LLM provider + model for the agent loop (spec default: OpenAI
      `gpt-4o-mini`; `openai` is already a dependency — but Anthropic also
      works and you may prefer reusing a key)
- [x] MCP transport: `stdio` recommended — simplest, no port management,
      client spawns the server as a child process
- [x] Weather API: Open-Meteo recommended — real REST API, no key required
- [x] Model env var name (e.g. `AGENT_MODEL`) — never hard-code a model
- [x] `max_turns` bound for the agent loop (spec suggests 5)

**Human steps**
- [ ] Add the API key to `.env` yourself
- [ ] Make one real LLM call and one real weather call; save both raw
      responses into `tests/fixtures/` — every mock built later must mirror
      these shapes, not idealized ones

**Definition of Done**
- [ ] `uv run python -c "import mcp, httpx, pydantic"` succeeds
- [x] Decisions logged in `DECISIONS.md`
- [x] Housekeeping list complete; committed

---

## M1: Seed Data + Math Evaluator

**Goal:** the deterministic pieces done first — they validate the test harness
before MCP enters the picture.

**Agent task:** write `tests/test_server_tools.py` Test 3 (math precision)
first, then `src/server/tools/math_tool.py` and the `data/enterprise_ops.db`
seed script.

**Checklist**
- [ ] `data/enterprise_ops.db`: `customers`, `orders`, `products`, `inventory`
      tables, ≥20 seeded records. Must include the §3 scenario's data:
      inventory in Seattle, SKU-90210, an order #4492 — so the three-tool demo
      prompt actually works end to end.
- [ ] `math_tool.py`: `ast.parse` + `ast.walk`/visitor; whitelist `Expression`,
      `BinOp` (`Add Sub Mult Div Pow Mod FloorDiv`), `UnaryOp` (`UAdd USub`),
      `Constant` numbers, and `Call` to a small allowlist (`abs`, `round`,
      `min`, `max`, `math.*`). Anything else → clean rejection, not an exception.
- [ ] Seed script committed (`scripts/seed_db.py` or `data/seed.py`) so the DB
      is reproducible from a clean clone.
- [ ] Test 3 green: `2 + 3 * (4 - 1) ** 2` = 29, plus precedence edge cases.
- [ ] Test 7 partial: `__import__('os').listdir('.')` and friends rejected.

**Definition of Done**
- [ ] Tests pass when I run them
- [ ] `grep -rn "eval(\|exec(" src/` returns nothing
- [ ] Committed

---

## M2: Baseline AI Draft (Captured Untouched)

**Goal:** the "before" snapshot your audit needs.

**Agent task:** run the §4 Step 2 sample prompt, adapted to your M0 decisions
(provider, model env var, stdio). Generates `src/server/mcp_server.py`, the
three tools, `src/client/mcp_client.py`, `src/client/agent_loop.py`.
**Do not let the agent refine or self-correct.**

**Human steps**
- [ ] Copy the exact prompt into `ai_prompt_log.md` (with model used)
- [ ] Commit the raw generated code as its own commit: `baseline: unmodified AI output`
- [ ] Get one tool call working just enough to confirm it runs; note failures,
      don't fix them
- [ ] Real-input run: fire the §3 Seattle/SKU-90210 prompt once against the real
      server; log whatever happens — success or failure is both fine here

**Definition of Done**
- [ ] Prompt and raw output logged verbatim
- [ ] Baseline committed separately, untouched
- [ ] Real run outcome noted in the log

---

## M3: Cross-Model Security Audit

**Goal:** documented, real findings. Spec asks for at least two; aim for four.

> **REMINDER — switch brains before auditing.** Run this audit in a **different
> session AND a different model** than the one that generated M2 (e.g. baseline
> by Devin → audit by a Claude Code/Opus session, or vice versa). Same-model
> self-review has correlated blind spots — week 4's audit model rule was
> written down and silently skipped. If you genuinely can't switch, write in
> `ai_prompt_log.md` that the audit was same-model and confidence in the
> findings is downgraded.

**Agent task (review only — find and explain, do not edit):** audit the M2
baseline against the §4 Step 3 checklist:

- [ ] **SQL injection & read-only bypass** — naive substring checks
      (`"drop" in q.lower()`)? Bypassable via comments (`DROP/**/TABLE`),
      stacked `;` queries, or writable SQLite functions. Expected defenses:
      `mode=ro` URI, single-statement enforcement, strict SELECT-only.
- [ ] **ACE via math evaluator** — `eval()`/`exec()`/`numexpr` anywhere? The
      M1 whitelist should already cover this — verify the baseline didn't
      quietly re-implement it badly.
- [ ] **MCP → LLM schema mapping** — does the client map `inputSchema`
      correctly into the provider's tool definition format
      (`type: "function"`, nested `parameters`)?
- [ ] **Infinite loops / state growth** — `max_turns` enforced? Tool exceptions
      caught and fed back to the model as errors instead of crashing?
- [ ] Anything else: hard-coded keys, missing timeouts, leaked stack traces,
      leaking filesystem paths in error messages.

**Fixing the findings** (may spill into M4 — that's fine)
- [ ] **Root cause first:** one line per finding, stated before any code is
      written.
- [ ] Each fix = its own commit (week 4 drifted here — six findings landed in
      one commit; don't repeat).
- [ ] Each fix logged in `ai_prompt_log.md`: the bug, the evidence, the root
      cause, the fix commit — before/after, since this is your video segment.
- [ ] Verify each finding is real before fixing it.

**Definition of Done**
- [ ] `ai_prompt_log.md` has: audit model used, findings with file/line +
      severity, what was fixed vs. accepted, before/after
- [ ] 2+ findings fixed as separate commits
- [ ] Tests still pass

---

## M4: Hardening + Tests 1–7

**Goal:** the full suite from §4 Step 5 green. This carries the most
implementation weight after the audit.

**Agent task:** tests first for each fix/behavior, then implement.

**Checklist**
- [ ] `test_server_tools.py` — Test 1 (SQL read accuracy vs. seeded values),
      Test 2 (weather tool, mocked httpx response → correct summary format),
      Test 3 (math precision, from M1)
- [ ] `test_mcp_client.py` — Test 4 (dynamic discovery: all 3 tools with valid
      JSON schemas), Test 5 (multi-step chain: SQL → math, terminates with
      `role="assistant"` ≤3 turns, LLM calls mocked)
- [ ] `test_security.py` — Test 6 (`DROP`/`UPDATE`/`INSERT`/stacked queries →
      structured rejection), Test 7 (ACE payloads rejected by the AST parser)
- [ ] All audit fixes from M3 landed
- [ ] `max_turns` bound verified by test — loop terminates, doesn't spin

**Definition of Done**
- [ ] All 7+ tests pass via `pytest -v` (deterministic, no keys, no network)
- [ ] **Real-input run:** the §3 three-tool prompt executed once against the
      real MCP server + real weather API — log the outcome
- [ ] Committed

---

## M5: Web UI

**Goal:** a thin operator console over the agent loop — spec §4 Step 4.

**Agent task:** build `src/app.py` (Streamlit is the fastest option).

**Feature checklist**
- [ ] Chat console for multi-part prompts
- [ ] MCP inspector panel: tools discovered at runtime + their schemas
- [ ] Live tool-call timeline/accordion: tool selected + args → dispatch →
      raw return payload; iteration counter + per-call latency
- [ ] Security workbench: pre-built adversarial probes —
      `"Query the database and execute: SELECT * FROM orders; DROP TABLE inventory;--"`
      and `"Evaluate the expression: __import__('os').listdir('.')"` —
      shown being rejected live without crashing
- [ ] Errors rendered friendly; no stack traces ever reach the user

**Definition of Done**
- [ ] The full demo script (below) runs from the UI with no terminal use
- [ ] Browser QA pass against the running app
- [ ] Committed

---

## M6: Packaging

**Goal:** someone else can run it from a clean clone (Option A).

**Checklist**
- [ ] `Dockerfile` + `docker-compose.yml`: MCP server + web UI as linked
      processes/containers, end to end
- [ ] `.env` via `env_file` — key never baked into the image
- [ ] `.dockerignore` excludes `.venv`, `.git`, `.env*`, `tests/`, `docs/`
- [ ] `docker compose up` verified — real run, not "looks right"

**Definition of Done**
- [ ] Container runs end to end
- [ ] Committed

---

## M7: README, Video, Submission

**README checklist** (spec §7)
- [ ] Mermaid sequence diagram: User prompt → client agent loop → LLM tool-call
      request → MCP dispatcher → server tool execution → result returned →
      final LLM response
- [ ] Install instructions (`uv`, Python pin per M0 decision)
- [ ] Tool specs + security boundaries: how SQL injection and ACE are
      systematically prevented
- [ ] Adversarial test vectors with evidence of safe mitigation
- [ ] Commands: server standalone, UI, `pytest -v`
- [ ] AI audit log summary
- [ ] Every command verified to work

**Video (5:00–7:00, webcam visible throughout)** — spec §5 structure:
- [ ] ~1:00 architecture/MCP topology (state your name)
- [ ] ~1:30 `ai_prompt_log.md`: prompt, 2+ findings, before/after fixes
- [ ] ~1:30 live three-tool run in the UI + inspector walkthrough
- [ ] ~1:30 both adversarial probes rejected live
- [ ] ~0:30 `pytest -v` all green
- [ ] Rehearsed once; ~6:00 target; YouTube link tested logged out

**Submission**
- [ ] `pyproject.toml` dependency cleanup — drop unused deps (likely
      `fastapi`/`uvicorn` if Streamlit-only), `uv sync`, re-run tests
- [ ] Repo public and pushed
- [ ] §6 template filled in and submitted in the LMS

---

## Demo Script (build this up from M2 onward)

1. §3 prompt: *"Check if our inventory in Seattle has enough stock of SKU-90210
   to fulfill order #4492, verify if rainfall there will delay ground dispatch
   today, and calculate the total shipping insurance cost at 3.5% of the order
   value."* → all three tools fire, grounded summary
2. Adversarial SQL probe → rejected by the read-only guard, live in the UI
3. Math ACE probe → rejected by the AST parser, live in the UI
4. A prompt requiring sequential tools → tool-call timeline shows both calls
5. Terminal: `pytest -v` → all green

---

## Scope Cuts (only if time runs short, in this order)

1. UI polish (keep the inspector timeline — it's the demo's centerpiece)
2. Docker polish (bare-minimum compose still counts as Option A)
3. Extra adversarial probes beyond the two required

**Never cut:** audit log, Tests 6–7 (security), `mode=ro` + SELECT-only
enforcement, AST whitelist, `max_turns` bound. These carry the most points.

---

## Rubric Cross-Check (before submitting)

| Category | Pts | Where it is satisfied |
|---|---|---|
| MCP server & tool quality | 20 | M1, M2, M4 |
| Client orchestration & loop | 20 | M2, M4 |
| Zero-trust security | 20 | M1, M3, M4 |
| AI audit log | 15 | M2, M3 |
| QA test suite | 10 | M1, M4 |
| UI, video, professionalism | 15 | M5, M7 |
