"""Tests 6–7: SQL injection / DDL rejection and math sandboxing (§4 Step 5)."""

import pytest

from src.server.tools.math_tool import calculate_expression
from src.server.tools.sql_tool import query_database

_SQL_PAYLOADS = [
    "DROP TABLE inventory",
    "UPDATE inventory SET quantity = 0",
    "INSERT INTO orders (id) VALUES (9999)",
    "DELETE FROM orders",
    "SELECT * FROM orders; DROP TABLE inventory;--",
    "SELECT * FROM orders; DELETE FROM orders",
    "SELECT/**/id/**/FROM/**/orders",
    "ATTACH DATABASE '/tmp/evil.db' AS evil",
    "SELECT load_extension('/tmp/x')",
]


@pytest.mark.parametrize("payload", _SQL_PAYLOADS)
async def test_sql_ddl_dml_rejection(payload):
    """Test 6: DDL/DML, stacked queries, and comments are all rejected."""
    result = await query_database(payload)
    assert result.startswith("Error")


async def test_readonly_guard_preserves_data():
    """After an injection attempt, the table is intact and still queryable."""
    await query_database("SELECT * FROM orders; DROP TABLE inventory;--")
    result = await query_database("SELECT COUNT(*) AS n FROM inventory")
    assert not result.startswith("Error")
    assert "8" in result


_ACE_PAYLOADS = [
    "__import__('os').listdir('.')",
    "__import__('os').system('id')",
    "().__class__.__bases__",
    "open('/etc/passwd').read()",
    "(1).__class__",
    "globals()",
    "x = 1",
]


@pytest.mark.parametrize("payload", _ACE_PAYLOADS)
def test_math_ace_blocked(payload):
    """Test 7: arbitrary-code payloads are rejected by the AST whitelist."""
    result = calculate_expression(payload)
    assert result.startswith("Error")
