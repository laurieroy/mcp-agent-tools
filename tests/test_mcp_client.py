"""Tests 4–5: client-server communication over real stdio transport (§4 Step 5)."""

from src.client.agent_loop import run_agent
from src.client.mcp_client import MCPClient


class _Block:
    """Duck-typed stand-in for an Anthropic content block."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _tool_use(block_id: str, name: str, arguments: dict) -> _Block:
    return _Block(type="tool_use", id=block_id, name=name, input=arguments)


def _text(text: str) -> _Block:
    return _Block(type="text", text=text)


def _response(*blocks: _Block) -> _Block:
    return _Block(content=list(blocks))


class _FakeMessages:
    def __init__(self, responses):
        self._responses = iter(responses)

    async def create(self, **kwargs):
        return next(self._responses)


class _FakeLLM:
    def __init__(self, responses):
        self.messages = _FakeMessages(responses)


async def test_dynamic_tool_discovery():
    """Test 4: the client discovers all 3 tools with valid JSON schemas."""
    async with MCPClient() as client:
        tools = await client.list_tools()
    assert {t["name"] for t in tools} == {
        "query_database",
        "get_current_weather",
        "calculate_expression",
    }
    for tool in tools:
        schema = tool["input_schema"]
        assert schema["type"] == "object"
        assert schema["properties"]


async def test_multi_step_chained_loop():
    """Test 5: SQL -> math chain terminates with an assistant answer <=3 turns."""
    llm = _FakeLLM(
        [
            _response(
                _tool_use(
                    "call_1",
                    "query_database",
                    {"sql_query": "SELECT total FROM orders WHERE id = 4492"},
                )
            ),
            _response(
                _tool_use(
                    "call_2",
                    "calculate_expression",
                    {"expression": "12800.0 * 0.035"},
                )
            ),
            _response(_text("Order #4492 totals $12,800; insurance is $448.")),
        ]
    )
    async with MCPClient() as client:
        result = await run_agent(
            "What is 3.5% insurance on order 4492?",
            client=client,
            llm=llm,
            model="test-model",
            max_turns=3,
        )
    assert result["turns"] <= 3
    assert "insurance" in result["answer"].lower()
    assert [t["tool"] for t in result["trace"]] == [
        "query_database",
        "calculate_expression",
    ]
    assert "12800" in result["trace"][0]["result"]
    assert "448" in result["trace"][1]["result"]
