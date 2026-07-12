"""Persistence Manager — Write-Ahead Log abstraction over SQLite."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from functools import partial
from typing import Any

from adapters.schemas import PersistenceRecord
from config.logging import get_logger

logger = get_logger(__name__)


class PersistenceManager:
    """Write-Ahead Log persistence backed by SQLite.

    Provides async read/write/checkpoint/recover operations
    using WAL mode for concurrent access safety.
    """

    def __init__(self, db_path: str = "sona_runtime.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def initialize(self) -> None:
        """Create database tables and enable WAL mode."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._setup_db)
        logger.info("persistence_initialized", db_path=self._db_path)

    async def write(self, category: str, key: str, value: dict[str, Any]) -> str:
        """Write a record to the persistence store.

        Returns the generated record_id.
        """
        record_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, partial(self._insert, record_id, category, key, value))
        return record_id

    async def read(self, category: str, key: str) -> dict[str, Any] | None:
        """Read the latest value for a category/key pair."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._select, category, key))

    async def list_category(self, category: str) -> list[PersistenceRecord]:
        """List all records in a category."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._list_cat, category))

    async def delete(self, record_id: str) -> bool:
        """Delete a record by ID. Returns True if deleted."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._delete, record_id))

    async def checkpoint(self, state: dict[str, Any]) -> str:
        """Create a checkpoint of the given state."""
        return await self.write("checkpoints", "latest", state)

    async def recover_latest(self) -> dict[str, Any] | None:
        """Recover the latest checkpoint."""
        return await self.read("checkpoints", "latest")

    async def shutdown(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        logger.info("persistence_shutdown")

    # --- Private synchronous helpers ---

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create the database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _setup_db(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_state (
                record_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at REAL NOT NULL DEFAULT (strftime('%s','now'))
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_category_key ON runtime_state(category, key)")
        conn.commit()

    def _insert(self, record_id: str, category: str, key: str, value: dict[str, Any]) -> None:
        """Insert a record into the database."""
        conn = self._get_conn()
        import time

        conn.execute(
            "INSERT INTO runtime_state (record_id, category, key, value, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (record_id, category, key, json.dumps(value), time.time()),
        )
        conn.commit()

    def _select(self, category: str, key: str) -> dict[str, Any] | None:
        """Select the latest record for a category/key pair."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT value FROM runtime_state WHERE category=? AND key=? "
            "ORDER BY created_at DESC LIMIT 1",
            (category, key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])  # type: ignore[no-any-return]

    def _list_cat(self, category: str) -> list[PersistenceRecord]:
        """List all records in a category."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT record_id, category, key, value, created_at "
            "FROM runtime_state WHERE category=? ORDER BY created_at DESC",
            (category,),
        )
        records: list[PersistenceRecord] = []
        for row in cursor.fetchall():
            records.append(
                PersistenceRecord(
                    record_id=row[0],
                    category=row[1],
                    key=row[2],
                    value=json.loads(row[3]),
                    created_at=row[4],
                )
            )
        return records

    def _delete(self, record_id: str) -> bool:
        """Delete a record by ID."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM runtime_state WHERE record_id=?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0
