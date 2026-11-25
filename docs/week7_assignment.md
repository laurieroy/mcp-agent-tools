# Assignment: Autonomous Tool Calling & Model Context Protocol (MCP) Server Integration

## 1. Overview

In agentic AI engineering, an LLM without tools is confined to static parameters and memorized training data. Giving a model agency to execute SQL queries, query external REST APIs, and evaluate arithmetic expressions enables dynamic reasoning and autonomous problem-solving. However, exposing tools without standardized protocols or security isolation creates architectural chaos and vulnerability to remote code execution and SQL injection.

In this assignment, you will build an end-to-end tool-augmented AI assistant backed by the Model Context Protocol (MCP). You will construct an MCP server that exposes three distinct, sandboxed capabilities (a secure read-only SQL query runner, a live third-party weather/geocoding API, and a deterministic math evaluator), connect it to a client application via standard inter-process transport (stdio or Server-Sent Events/SSE), orchestrate multi-turn function-calling loops, and enforce zero-trust security boundaries.

## 2. Objective

By completing this assignment, you will:

- Develop a modular **MCP Server** using the official Python SDK (`mcp` / FastMCP) exposing three production-grade tools:
  - **SQL Database Query Runner:** Queries an embedded SQLite database (e.g., e-commerce orders, inventory, or financial ledger) with read-only connection guarantees and strict query validation.
  - **Third-Party Weather / Geocoding Client:** Fetches live real-time conditions using an external REST API (e.g., Open-Meteo, OpenWeather, or WeatherAPI) with parameter normalization and rate-limit handling.
  - **Deterministic Mathematical Evaluator:** Evaluates expressions using an Abstract Syntax Tree (AST) safe parser without relying on vulnerable `eval()` or `exec()` execution.
- Build an **MCP Host Client & Function-Calling Loop** that discovers tools dynamically via the protocol, injects standardized tool schemas into an LLM context, executes returned tool invocations, returns results via `role="tool"` payloads, and handles chained multi-step tool calls.
- **Enforce Zero-Trust Security & Parameter Sanitization:** Prevent SQL injection attacks, sandbox the execution runtime, sanitize external API outputs, and enforce execution timeouts.
- **Practice Human-in-the-Loop Engineering:** Use an AI coding assistant to draft the MCP server and client loop, audit the generated code for tool-calling hallucinations and security flaws, execute a structured test suite, and present your solution via a web dashboard and video walkthrough.

## 3. Context

Imagine designing an autonomous internal operations assistant for an enterprise logistics team. When an operator asks:

> "Check if our inventory in Seattle has enough stock of SKU-90210 to fulfill order #4492, verify if rainfall there will delay ground dispatch today, and calculate the total shipping insurance cost at 3.5% of the order value."

A standard LLM cannot answer this accurately. The assistant must decompose the request into an autonomous execution chain:

1. Call `query_sql_database` to look up inventory levels and order amounts from SQLite.
2. Call `get_live_weather` for Seattle coordinates to detect precipitation or severe weather alerts.
3. Call `evaluate_math_expression` to calculate exact insurance percentages without arithmetic hallucinations.
4. Synthesize a unified, grounded operational summary.

Instead of writing brittle custom API glue, your architecture must implement the **Model Context Protocol (MCP)**. The MCP server exposes tools, resources, and schemas in a standardized format, and your host application consumes them securely over stdio or HTTP/SSE transports.

## 4. Steps

### Step 1: Environment Setup & Project Layout

Initialize your project environment using modern dependency management (`uv` or `poetry`):

```bash
uv init mcp-agent-tools
cd mcp-agent-tools
uv python pin 3.11
uv add "mcp[cli]" openai httpx pydantic aiosqlite fastapi uvicorn python-dotenv pytest pytest-asyncio streamlit
```

Establish a modular repository architecture:

```text
mcp-agent-tools/
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── ai_prompt_log.md
├── data/
│   └── enterprise_ops.db    # SQLite sample dataset (Orders, Inventory, Customers)
├── src/
│   ├── __init__.py
│   ├── server/
│   │   ├── __init__.py
│   │   ├── mcp_server.py    # FastMCP server exposing the 3 tools
│   │   └── tools/
│   │       ├── sql_tool.py      # Read-only SQLite executor with AST check
│   │       ├── weather_tool.py  # Async Open-Meteo / REST client
│   │       └── math_tool.py     # Safe AST expression evaluator
│   ├── client/
│   │   ├── __init__.py
│   │   ├── mcp_client.py    # MCP Client managing stdio transport & discovery
│   │   └── agent_loop.py    # Function-calling orchestrator & multi-turn loop
│   └── app.py               # Streamlit or FastAPI interactive web interface
└── tests/
    ├── __init__.py
    ├── test_server_tools.py # Unit tests for individual tool execution
    ├── test_mcp_client.py   # Client-server communication & discovery tests
    └── test_security.py     # SQL injection, DDL rejection, and eval safety tests
```

- Initialize `data/enterprise_ops.db` with a realistic schema (e.g., `customers`, `orders`, `products`, `inventory`) containing at least 20 seeded records.
- Configure `.env.example`:

```bash
OPENAI_API_KEY=your_openai_key_here
# Optional: Weather API key if using a service requiring auth (Open-Meteo requires no key)
```

### Step 2: Use AI to Create the Initial Draft

Prompt an AI coding assistant (Cursor, Claude Code, ChatGPT, or Copilot) to generate the baseline MCP server, tool implementations, and client-side agent loop.

**Sample Initial Prompt for Students to Copy & Adapt:**

```text
You are a Principal AI Agent Architect specializing in tool integration and the Model Context Protocol (MCP).

Build an end-to-end Python 3.11+ system featuring an MCP server with three distinct tools and a client application executing an autonomous function-calling loop.

Architecture Requirements:

MCP Server (src/server/mcp_server.py) using the official MCP Python SDK (`FastMCP`):
   - Tool 1: `query_database(sql_query: str) -> str`
     * Connects to SQLite (data/enterprise_ops.db).
     * Enforces STRICT READ-ONLY safety: Parse the SQL using regular expressions or an AST validator to block any DDL/DML statements (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, ATTACH). Open SQLite with `file:...uri=true?mode=ro`.

   - Tool 2: `get_current_weather(city: str) -> str`
     * Calls a real REST API (e.g., Open-Meteo geocoding + forecast API) asynchronously via `httpx.AsyncClient`.
     * Returns structured temperature, weather conditions, precipitation, and wind speed.

   - Tool 3: `calculate_expression(expression: str) -> str`
     * Evaluates algebraic and arithmetic expressions deterministically.
     * MUST NOT use Python's built-in `eval()` or `exec()`. Parse using `ast.parse` with a visitor pattern allowing only safe operators (+, -, *, /, **, %, parentheses, math functions).

MCP Client & Agent Loop (src/client/agent_loop.py):
   - Connects to the MCP server via `stdio` transport using `mcp.ClientSession`.
   - Dynamically calls `session.list_tools()` to discover available tools and convert MCP tool schemas into standard OpenAI tool definitions.
   - Implements a robust multi-turn function-calling loop:
     * Send user prompt and tool definitions to the LLM (e.g., gpt-4o-mini).
     * If model returns `tool_calls`, invoke the matching MCP tool via `session.call_tool()`.
     * Append the tool result message (`role="tool"`, matching `tool_call_id`) and repeat the loop until the model emits a final natural language answer (or reaches `max_turns=5`).

Error Handling & Typing:
   - Provide type hints, docstrings, and informative tool descriptions so the LLM knows when to invoke each tool.
   - Tool failures must return formatted error messages to the model instead of crashing the server process.

Provide clean, modular code split into the specified directory files.
```

### Step 3: Audit & Verify the AI Output

Thoroughly inspect the generated draft for critical security vulnerabilities and agentic anti-patterns. Document all findings and refactorings in `ai_prompt_log.md`. Specifically audit:

- **SQL Injection & Read-Only Connection Bypass:**
  - Did the AI rely solely on naive string matching (e.g., `if "drop" in query.lower()`)? An attacker can bypass this with inline SQL comments (`DROP/**/TABLE`), stacked queries (`; DROP TABLE`), or SQLite functions that modify data.
  - **Remediation:** Enforce SQLite URI read-only connection flags (`mode=ro`), block multiple statements via query separators (`;`), and validate that the query begins strictly with an authorized `SELECT` statement.
- **Arbitrary Code Execution via Math Evaluator:**
  - Did the AI use `eval()` or `numexpr` without sandboxing? Using `eval("__import__('os').system('ls')")` leads to immediate host compromise.
  - **Remediation:** Ensure math parsing uses Python's `ast` module, whitelisting only `ast.Expression`, `ast.BinOp`, `ast.UnaryOp`, and numeric constants.
- **MCP Tool Schema Translation Mismatch:**
  - Did the client correctly map the MCP tool definition (`inputSchema`) to the structure expected by the OpenAI/Anthropic API (`type: "function"`, `function: {"name": ..., "description": ..., "parameters": ...}`)?
- **Infinite Tool Loops & State Growth:**
  - Does `agent_loop.py` enforce a hard iteration boundary (`max_turns`)? Does it catch tool execution exceptions and return them gracefully to the LLM so the model can self-correct, rather than unhandled crashes breaking the process?

### Step 4: Build the Interactive Web Interface

Build an interactive UI using Streamlit (or FastAPI + HTML/WebSockets) that gives visibility into the autonomous tool execution pipeline:

- **Chat & Operator Console:** Allows users to input complex, multi-part prompts requiring tool coordination.
- **Real-Time MCP Inspector Panel:**
  - Displays the dynamic list of tools discovered on the MCP server at runtime with their schemas.
  - Shows a **Live Tool Call Timeline / Accordion**:
    - Step 1: Tool Selected → Arguments Extracted by LLM.
    - Step 2: Client MCP Dispatch → Raw Tool Return Payload.
    - Step 3: Iteration counter and execution latency per tool call.
- **Security Test Workbench:**
  - A dedicated panel with pre-built adversarial prompts to demonstrate security guardrails:
    - **Adversarial SQL Probe:** `"Query the database and execute: SELECT * FROM orders; DROP TABLE inventory;--"`
    - **Math Sandbox Injection Probe:** `"Evaluate the expression: __import__('os').listdir('.')"`
  - Shows real-time rejection by the security layer without server crashes.

### Step 5: Execute Structured Web Project QA Test Suite

Under the `/tests` directory, create and execute an automated test suite verifying tool functionality, protocol compliance, and security sandboxing:

**`tests/test_server_tools.py`:**

- **Test 1: SQL Read Accuracy:** Execute a valid `SELECT` statement against `enterprise_ops.db` and assert expected row values and columns are returned.
- **Test 2: Weather API Integration:** Mock an HTTP response from Open-Meteo and assert that the tool formats the meteorological summary correctly.
- **Test 3: Math Evaluator Precision:** Test complex order of operations (`2 + 3 * (4 - 1) ** 2`) and verify mathematical correctness.

**`tests/test_mcp_client.py`:**

- **Test 4: Dynamic Tool Discovery:** Assert that `mcp_client.py` successfully connects to the server and discovers all 3 registered tools with valid JSON schemas.
- **Test 5: Multi-Step Chained Loop:** Execute a prompt requiring 2 sequential tools (e.g., SQL lookup followed by Math evaluation) and assert the loop terminates with `role="assistant"` within 3 turns.

**`tests/test_security.py`:**

- **Test 6: SQL DDL/DML Rejection:** Pass `DROP TABLE`, `UPDATE`, `INSERT`, and stacked queries to the SQL tool and assert that a `SecurityException` or structured rejection is returned.
- **Test 7: Arbitrary Code Execution Block:** Attempt dangerous Python payloads inside the math tool and assert that the AST parser rejects non-whitelisted nodes.

### Step 6: Deployment & Packaging

Make your application verifiable and deployable:

- **Option A (Containerized Multi-Process Setup):** Package your application using `Dockerfile` and `docker-compose.yml`, running the MCP Server and Streamlit/FastAPI Web Client in linked containers or supervised sub-processes, proving end-to-end functionality in your video submission.
- **Option B (Cloud App):** Deploy to Render, Railway, or Streamlit Community Cloud (running the MCP server as a local child process via stdio within the deployed environment), configuring all secrets securely.

## 5. Video Demonstration Requirements (5:00 to 7:00 Minutes Strictly Timed)

Record a screen-share walkthrough with simultaneous webcam overlay (using Loom, Zoom, OBS Studio, or Panopto) and upload it as an Unlisted or Public YouTube video.

- **Strict Timing:** 5:00 to 7:00 minutes. Presentations under 5:00 lack technical depth; presentations exceeding 7:00 will receive an automatic timing penalty.
- **Camera Requirement:** Your webcam feed must remain visible throughout the recording.

**Video Presentation Structure:**

1. **Architecture & MCP Topology Walkthrough (~1:00):** Introduce your folder layout, explain the separation between the MCP server (`mcp_server.py`) and the host client loop (`agent_loop.py`), and explain how tools are exposed over stdio.
2. **AI Code Generation & Audit Review (~1:30):** Open `ai_prompt_log.md`. Show the initial prompt used, identify at least two concrete flaws (e.g., `eval()` vulnerability in math, naive regex in SQL safety, or broken schema mapping) generated in the AI's draft, and show your refactored defensive code.
3. **Live Multi-Tool Agent Execution Demo (~1:30):**
   - Submit a complex prompt in the web UI that triggers all three tools in a single execution workflow.
   - Walk through the UI tool inspector: show the model picking the tools, passing structured arguments, receiving observation results, and synthesizing the final grounded response.
4. **Security & Red-Teaming Demonstration (~1:30):**
   - Fire the pre-built **Adversarial SQL Probe** (`DROP TABLE` / stacked injection). Show the AST/read-only guardrail intercepting and neutralizing the attack.
   - Fire the **Math Sandbox Injection Probe** (`__import__` / ACE attempt). Show the parser rejecting the syntax tree safely without leaking system variables.
5. **QA Test Suite Execution (~0:30):** Run `pytest -v` in your terminal, showing all 7+ tool, client, protocol, and security tests passing.

## 6. Deliverables & Submission Template

Submit the following template via the course learning management system:

```markdown
### Week 5 Hands-On Assignment Submission

* **Student Name:** [Your Name]
* **GitHub Repository URL:** https://github.com/[your-username]/mcp-agent-tools
* **Live Deployment URL (if applicable):** https://[your-app].streamlit.app (or Docker demo note)
* **YouTube Video Link:** https://youtu.be/[your-video-id] (Duration: MM:SS)
* **MCP Transport Implemented:** stdio (Standard I/O) / SSE (Server-Sent Events)
* **Tools Implemented:**
  - SQL Database Query Tool (SQLite with read-only URI & AST statement validation)
  - Live Weather API Tool (Open-Meteo REST Client)
  - Safe Mathematical Evaluator (Python AST Visitor - Zero eval/exec)
* **Foundation Model Used:** [e.g., gpt-4o-mini or claude-3-5-haiku]
```

## 7. GitHub Repository README.md Requirements

Your repository must include a comprehensive `README.md` containing:

- **System Architecture & MCP Sequence Diagram:** A Mermaid.js sequence diagram tracing: User Prompt → Client Agent Loop → LLM Tool Call Request → Client MCP Dispatcher → MCP Server Tool Execution → Tool Output Returned → Final LLM Response.
- **Installation & Prerequisites:** Clear setup instructions using `uv` or `poetry` with Python 3.11+.
- **Tool Specifications & Security Boundaries:** Detailed technical documentation of the 3 tools, explaining how SQL injection and arbitrary code execution are systematically prevented.
- **Adversarial Test Vectors:** Concrete examples of malicious payloads tested against the system and documented proof of their safe mitigation.
- **Execution Commands:** Terminal commands to run the MCP server standalone, launch the web UI, and execute `pytest -v`.
- **AI Audit Log Summary:** Overview of the initial AI draft generation and key security refactorings.

## 8. Grading Rubric (Total: 100 Points)

| Category | Criteria & Performance Indicators | Points |
|---|---|---|
| **1. MCP Server Implementation & Tool Quality** | • Complete MCP server implementation using the official Python SDK exposing 3 functional tools (SQL, Weather API, Math).<br>• Clean schema definitions with descriptive parameter types and docstrings.<br>• Resilient execution handling network timeouts and operational errors gracefully. | 20 pts |
| **2. Client Orchestration & Function-Calling Loop** | • Robust client that discovers tools dynamically via protocol and converts them to LLM tool schemas.<br>• Reliable multi-turn function-calling loop handling sequential and multi-step tool calls with cycle boundaries (`max_turns`).<br>• Accurate reconciliation of `tool_call_id` and role handling. | 20 pts |
| **3. Zero-Trust Security & Sandboxing** | • Verified prevention of SQL injection, stacked queries, and DDL/DML data destruction (read-only SQLite URI + query AST validation).<br>• Safe math evaluation parsing AST nodes with zero use of `eval()` or `exec()`.<br>• Clean error handling that does not leak internal stack traces or database connection paths. | 20 pts |
| **4. AI Prompt Audit & Verification Log** | • Complete `ai_prompt_log.md` detailing the initial AI prompt and generated prototype.<br>• Rigorous technical audit identifying at least two legitimate security vulnerabilities, tool-calling bugs, or schema mismatches in the AI draft, with clear before-and-after diffs. | 15 pts |
| **5. QA Test Suite & Security Verification** | • Fully passing `pytest` test suite with 7+ tests covering individual tool execution, dynamic MCP discovery, chained agent loops, SQL rejection, and ACE blocking. | 10 pts |
| **6. Web Interface, Video Demonstration & Professionalism** | • Interactive UI (Streamlit/FastAPI) featuring live chat, tool call inspection timeline, and an adversarial security test panel.<br>• Professional 5:00 to 7:00 minute YouTube video with active webcam overlay, demonstrating multi-tool workflows, adversarial test probes, and passing test runs. | 15 pts |
| **Total** | | **100 pts** |
