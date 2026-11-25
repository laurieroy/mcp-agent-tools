"""Read-only SQLite query tool with strict single-SELECT validation.

Defense layers (in order):
1. Query validation: exactly one statement, no ``;`` stacking, no SQL
   comments, must start with SELECT, and no DDL/DML keywords anywhere
   outside string literals.
2. The SQLite connection itself is opened read-only via a
   ``file:...?mode=ro`` URI, so writes fail even if a statement slipped past
   validation.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import aiosqlite

_REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = _REPO_ROOT / "data" / "enterprise_ops.db"
_MAX_ROWS = 100

_BLOCKED_KEYWORDS = (
    "drop", "delete", "update", "insert", "alter", "truncate", "attach",
    "detach", "create", "replace", "pragma", "vacuum", "reindex",
)
_KEYWORD_RE = re.compile(r"\b(" + "|".join(_BLOCKED_KEYWORDS) + r")\b", re.IGNORECASE)
_STRING_LITERAL_RE = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"")
_SELECT_RE = re.compile(r"select\b", re.IGNORECASE)


def validate_sql(sql_query: str) -> str | None:
    """Return ``None`` if the query is safe to run, else a rejection reason."""
    q = sql_query.strip()
    if not q:
        return "empty query"
    if q.endswith(";"):
        q = q[:-1].rstrip()
    if ";" in q:
        return "multiple statements are not allowed"
    if "--" in q or "/*" in q:
        return "SQL comments are not allowed"
    # Scan the query with string literals removed so keywords inside quotes
    # (e.g. WHERE status = 'update') can't trigger or evade the checks.
    scrubbed = _STRING_LITERAL_RE.sub(" ", q).lstrip()
    if not _SELECT_RE.match(scrubbed):
        return "only SELECT statements are allowed"
    match = _KEYWORD_RE.search(scrubbed)
    if match:
        return f"keyword '{match.group(1).upper()}' is not allowed"
    return None


async def query_database(sql_query: str) -> str:
    """Run a single read-only SELECT against ``data/enterprise_ops.db``.

    Returns a pipe-delimited table (header + up to 100 rows) or a
    ``"Error: ..."`` string. Never raises to the caller.
    """
    rejection = validate_sql(sql_query)
    if rejection:
        return f"Error: query rejected ({rejection})"

    try:
        async with aiosqlite.connect(f"file:{DB_PATH}?mode=ro", uri=True) as db:
            async with db.execute(sql_query) as cursor:
                columns = [d[0] for d in cursor.description or []]
                rows = await cursor.fetchmany(_MAX_ROWS)
    except sqlite3.Error as exc:
        return f"Error: {exc}"

    if not columns:
        return "Query returned no result set."
    lines = [" | ".join(columns)]
    if not rows:
        lines.append("(0 rows)")
    else:
        lines += [" | ".join("" if v is None else str(v) for v in row) for row in rows]
        if len(rows) == _MAX_ROWS:
            lines.append(f"... truncated at {_MAX_ROWS} rows")
    return "\n".join(lines)
