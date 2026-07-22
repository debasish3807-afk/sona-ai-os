"""Database Tool — SQLite query execution with read/write support.

Provides safe database operations with:
    - SQLite database creation and connection
    - Read queries (SELECT) — always allowed
    - Write queries (INSERT, UPDATE, DELETE, CREATE) — permission gated
    - Single-statement enforcement (defense-in-depth against injection)
    - Query result formatting
    - Database path workspace restriction
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path
from typing import Any

from config.logging import get_logger
from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParam, ToolResult
from tools.permissions import ToolPermissions

logger = get_logger(__name__)

# SQL statements considered write operations
WRITE_KEYWORDS = {"insert", "update", "delete", "drop", "alter", "create", "replace", "truncate"}


def _is_write_query(sql: str) -> bool:
    """Determine if a SQL statement modifies data."""
    first_word = sql.strip().split()[0].lower() if sql.strip() else ""
    return first_word in WRITE_KEYWORDS


def _validate_query(sql: str) -> None:
    """Validate a SQL query for safety (single-statement enforcement).

    Raises ValueError if the query contains multiple statements.

    This provides defense-in-depth against SQL injection via multi-statement
    execution. Parameterized queries are the primary defense.
    """
    stripped = sql.strip()
    if not stripped:
        raise ValueError("Empty query")

    # Check for multiple statements (semicolons not inside string literals)
    in_single_quote = False
    in_double_quote = False
    for i, ch in enumerate(stripped):
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif ch == ";" and not (in_single_quote or in_double_quote):
            # Semicolons inside string literals are fine
            remaining = stripped[i:].lstrip(";").strip()
            if remaining:
                raise ValueError(
                    "Multiple SQL statements are not allowed. "
                    "Use parameterized queries for dynamic values."
                )
            break


def _format_results(columns: list[str], rows: list[tuple[Any, ...]]) -> str:
    """Format query results as a readable table."""
    if not rows:
        return "(no rows returned)"

    # Calculate column widths
    col_widths = [len(c) for c in columns]
    for row in rows[:100]:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)[:50]))

    # Build header
    header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
    separator = "-+-".join("-" * w for w in col_widths)

    # Build rows
    lines = [header, separator]
    for row in rows[:100]:
        line = " | ".join(str(val)[:50].ljust(col_widths[i]) for i, val in enumerate(row))
        lines.append(line)

    if len(rows) > 100:
        lines.append(f"\n... ({len(rows)} total rows, showing first 100)")

    return "\n".join(lines)


class DatabaseQueryTool(BaseTool):
    """Execute a SQL query against a SQLite database."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="db_query",
            description="Execute a SQL query against a SQLite database file",
            category=ToolCategory.DATABASE,
            parameters=[
                ToolParam("database", "string", "Path to SQLite database file"),
                ToolParam("query", "string", "SQL query to execute"),
                ToolParam(
                    "params", "array", "Query parameters for parameterized queries", required=False
                ),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        db_path = str(params.get("database", ""))
        query = str(params.get("query", ""))
        query_params = params.get("params") or []

        if not db_path or not query:
            return ToolResult(success=False, error="Both 'database' and 'query' are required")

        resolved = str(Path(db_path).resolve())
        if not self._permissions.is_path_allowed(resolved):
            return ToolResult(success=False, error=f"Access denied: {db_path} is outside workspace")

        # Check write permission
        is_write = _is_write_query(query)
        if is_write and self._permissions.level < 50:
            return ToolResult(
                success=False, error="Write queries require STANDARD permission level or higher"
            )

        # Validate query safety
        try:
            _validate_query(query)
        except ValueError as exc:
            return ToolResult(success=False, error=f"Query validation failed: {exc}")

        # Execute in thread pool to avoid blocking
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._execute_sync, resolved, query, query_params, is_write
            )
            return result
        except Exception as exc:
            return ToolResult(success=False, error=f"Database error: {exc}")

    def _execute_sync(
        self, db_path: str, query: str, query_params: list[Any], is_write: bool
    ) -> ToolResult:
        """Synchronous database execution (runs in thread pool)."""
        try:
            conn = sqlite3.connect(db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if query_params:
                cursor.execute(query, query_params)
            else:
                cursor.execute(query)

            if is_write:
                conn.commit()
                affected = cursor.rowcount
                return ToolResult(
                    success=True,
                    output=f"Query executed successfully. Rows affected: {affected}",
                    data={"rows_affected": affected, "is_write": True},
                )

            # Read query — fetch results
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            raw_rows = [tuple(row) for row in rows]

            output = _format_results(columns, raw_rows)
            return ToolResult(
                success=True,
                output=output,
                data={
                    "columns": columns,
                    "row_count": len(raw_rows),
                    "is_write": False,
                },
            )

        except sqlite3.Error as exc:
            return ToolResult(success=False, error=f"SQLite error: {exc}")
        finally:
            import contextlib

            with contextlib.suppress(Exception):
                conn.close()


class DatabaseSchemaTool(BaseTool):
    """Show database schema (tables and columns)."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="db_schema",
            description="Show the schema of a SQLite database (tables, columns, types)",
            category=ToolCategory.DATABASE,
            parameters=[
                ToolParam("database", "string", "Path to SQLite database file"),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        db_path = str(params.get("database", ""))
        if not db_path:
            return ToolResult(success=False, error="Parameter 'database' is required")

        resolved = str(Path(db_path).resolve())
        if not self._permissions.is_path_allowed(resolved):
            return ToolResult(success=False, error=f"Access denied: {db_path} is outside workspace")

        if not os.path.isfile(resolved):
            return ToolResult(success=False, error=f"Database file not found: {db_path}")

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._get_schema, resolved
            )
            return result
        except Exception as exc:
            return ToolResult(success=False, error=f"Schema error: {exc}")

    def _get_schema(self, db_path: str) -> ToolResult:
        """Get database schema synchronously."""
        try:
            conn = sqlite3.connect(db_path, timeout=10.0)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]

            if not tables:
                return ToolResult(
                    success=True, output="(empty database — no tables)", data={"tables": []}
                )

            lines: list[str] = []
            table_info: dict[str, list[str]] = {}

            for table in tables:
                # Validate table name to prevent SQL injection via malicious table names
                if not table or not isinstance(table, str) or not table.isidentifier():
                    logger.warning("Skipping table with invalid name", table=table)
                    continue

                cursor.execute(f"PRAGMA table_info({table})")  # noqa: S608 — table validated
                columns = cursor.fetchall()
                col_defs: list[str] = []
                for col in columns:
                    name = col[1]
                    col_type = col[2] or "TEXT"
                    pk = " PRIMARY KEY" if col[5] else ""
                    not_null = " NOT NULL" if col[3] else ""
                    col_defs.append(f"    {name} {col_type}{pk}{not_null}")

                lines.append(f"TABLE {table}:")
                lines.extend(col_defs)
                lines.append("")
                table_info[table] = [c[1] for c in columns]

            conn.close()
            return ToolResult(
                success=True,
                output="\n".join(lines),
                data={"tables": tables, "schema": table_info},
            )

        except sqlite3.Error as exc:
            return ToolResult(success=False, error=f"SQLite error: {exc}")


def register_database_tools(permissions: ToolPermissions) -> list[BaseTool]:
    """Create and return all database tool instances."""
    return [
        DatabaseQueryTool(permissions),
        DatabaseSchemaTool(permissions),
    ]
