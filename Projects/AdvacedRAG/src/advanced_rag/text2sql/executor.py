"""SQL validation and read-only execution.

Two independent gates stand between a generated string and the database:

1. `validate()` - a static check that rejects anything that is not a single
   read-only SELECT. It runs before a human ever sees the query.
2. Human approval - enforced by the graph, which interrupts and will not call
   `execute()` until the proposal comes back approved.

The validator is deliberately conservative: it rejects on suspicion rather than
trying to sanitise, because a rejected query costs one retry and an accepted bad
one costs a production incident.
"""

from __future__ import annotations

import logging
import re

from sqlalchemy import text

from advanced_rag.config import Settings, get_settings
from advanced_rag.guardrails import patterns
from advanced_rag.text2sql.database import QueryResult, get_engine

logger = logging.getLogger(__name__)

_LEADING_CTE = re.compile(r"^\s*WITH\b", re.I)
_LEADING_SELECT = re.compile(r"^\s*SELECT\b", re.I)
_LIMIT = re.compile(r"\bLIMIT\s+(\d+)\b", re.I)


class SqlRejected(ValueError):
    """The generated SQL failed static validation and must not run."""


def normalize(sql: str) -> str:
    """Strip markdown fences and the trailing semicolon the model likes to add."""
    cleaned = sql.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?\s*|\s*```$", "", cleaned, flags=re.I).strip()
    return cleaned.rstrip(";").strip()


def validate(sql: str, settings: Settings | None = None) -> str:
    """Return the query with an enforced LIMIT, or raise SqlRejected."""
    settings = settings or get_settings()
    query = normalize(sql)
    if not query:
        raise SqlRejected("the generated query was empty")

    if not (_LEADING_SELECT.match(query) or _LEADING_CTE.match(query)):
        raise SqlRejected("only SELECT (or WITH ... SELECT) queries are allowed")

    # A semicolon anywhere but the (already stripped) end means stacked statements.
    if ";" in query:
        raise SqlRejected("multiple statements are not allowed")

    for pattern in patterns.SQL_WRITE_PATTERNS:
        match = pattern.search(query)
        if match:
            raise SqlRejected(f"query contains a forbidden construct: {match.group(0)!r}")

    return _enforce_limit(query, settings.sql_row_limit)


def _enforce_limit(query: str, row_limit: int) -> str:
    found = _LIMIT.search(query)
    if not found:
        return f"{query} LIMIT {row_limit}"
    if int(found.group(1)) > row_limit:
        # Clamp rather than reject: the query is fine, the bound is not.
        logger.info("Clamping LIMIT %s to %d", found.group(1), row_limit)
        return _LIMIT.sub(f"LIMIT {row_limit}", query, count=1)
    return query


def execute(sql: str, settings: Settings | None = None) -> QueryResult:
    """Run a validated read-only query inside a rolled-back transaction.

    The rollback is belt-and-braces: `validate()` has already rejected writes,
    but a connection that can never commit means a validator bug cannot mutate
    anything either.
    """
    settings = settings or get_settings()
    query = validate(sql, settings)
    engine = get_engine(settings)

    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            if settings.postgres_dsn:
                # Bound the query server-side too, so a cartesian join cannot
                # hold a connection open indefinitely.
                conn.execute(
                    text(f"SET LOCAL statement_timeout = '{settings.sql_timeout_seconds}s'")
                )
                conn.execute(text("SET LOCAL transaction_read_only = on"))
            result = conn.execute(text(query))
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchmany(settings.sql_row_limit + 1)]
        finally:
            transaction.rollback()

    truncated = len(rows) > settings.sql_row_limit
    return QueryResult(
        columns=columns, rows=rows[: settings.sql_row_limit], truncated=truncated
    )


def render_rows(result: QueryResult, max_rows: int = 25) -> str:
    """Compact text table for the answer prompt and the UI."""
    if not result.columns:
        return "(no columns)"
    if not result.rows:
        return "(no rows matched)"

    shown = result.rows[:max_rows]
    widths = [len(c) for c in result.columns]
    for row in shown:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(_cell(value)))

    header = " | ".join(c.ljust(widths[i]) for i, c in enumerate(result.columns))
    divider = "-+-".join("-" * width for width in widths)
    body = [
        " | ".join(_cell(v).ljust(widths[i]) for i, v in enumerate(row)) for row in shown
    ]
    footer = []
    if len(result.rows) > max_rows:
        footer.append(f"... {len(result.rows) - max_rows} more rows")
    if result.truncated:
        footer.append("(result set truncated at the configured row limit)")
    return "\n".join([header, divider, *body, *footer])


def _cell(value: object) -> str:
    return "NULL" if value is None else str(value)
