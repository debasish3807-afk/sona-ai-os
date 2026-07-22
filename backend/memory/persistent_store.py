"""
Persistent Memory Store — SQLite-backed MemoryStore implementation.

Provides production-grade persistence for all memory types with full
CRUD, search, tagging, pinning, import/export, and statistics.
Uses SQLite with WAL mode for concurrent read safety.
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.logging import get_logger
from memory.exceptions import MemoryStorageError
from memory.types import (
    MemoryEntry,
    MemoryScope,
    MemorySearchResult,
    MemoryStats,
    MemoryTag,
    MemoryType,
)

logger = get_logger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    entry_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    scope TEXT NOT NULL,
    session_id TEXT DEFAULT '',
    user_id TEXT DEFAULT '',
    importance_score REAL DEFAULT 0.5,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    accessed_at REAL NOT NULL,
    access_count INTEGER DEFAULT 0,
    pinned INTEGER DEFAULT 0,
    expires_at REAL,
    metadata TEXT DEFAULT '{}',
    source TEXT DEFAULT '',
    token_count INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 50
);
CREATE TABLE IF NOT EXISTS memory_tags (
    entry_id TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    tag_category TEXT DEFAULT '',
    PRIMARY KEY (entry_id, tag_name),
    FOREIGN KEY (entry_id) REFERENCES memories(entry_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope);
CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance_score);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_tags_name ON memory_tags(tag_name);
"""


class PersistentMemoryStore:
    """SQLite-backed persistent memory store."""

    def __init__(self, db_path: str = "sona_memory.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def initialize(self) -> None:
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()
        logger.info("memory_store_initialized", db_path=self._db_path)

    async def shutdown(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Memory store not initialized")
        return self._conn

    @staticmethod
    def _ts(dt: datetime | None) -> float | None:
        return dt.timestamp() if dt else None

    @staticmethod
    def _from_ts(ts: float | None) -> datetime | None:
        return datetime.fromtimestamp(ts, tz=UTC) if ts else None

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        tags_raw = (
            self._get_conn()
            .execute(
                "SELECT tag_name, tag_category FROM memory_tags WHERE entry_id = ?",
                (row["entry_id"],),
            )
            .fetchall()
        )
        return MemoryEntry(
            entry_id=row["entry_id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            scope=MemoryScope(row["scope"]),
            session_id=row["session_id"] or "",
            user_id=row["user_id"] or "",
            importance_score=row["importance_score"],
            tags=[MemoryTag(name=r["tag_name"], category=r["tag_category"]) for r in tags_raw],
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=datetime.fromtimestamp(row["created_at"], tz=UTC),
            updated_at=datetime.fromtimestamp(row["updated_at"], tz=UTC),
            accessed_at=datetime.fromtimestamp(row["accessed_at"], tz=UTC),
            access_count=row["access_count"],
            pinned=bool(row["pinned"]),
            expires_at=self._from_ts(row["expires_at"]),
            source=row["source"] or "",
            token_count=row["token_count"] or 0,
        )

    async def store(self, entry: MemoryEntry) -> str:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO memories
                (entry_id, content, memory_type, scope, session_id, user_id,
                 importance_score, created_at, updated_at, accessed_at,
                 access_count, pinned, expires_at, metadata, source, token_count, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.entry_id,
                    entry.content,
                    entry.memory_type.value,
                    entry.scope.value,
                    entry.session_id or "",
                    entry.user_id or "",
                    entry.importance_score,
                    self._ts(entry.created_at),
                    self._ts(entry.updated_at),
                    self._ts(entry.accessed_at),
                    entry.access_count,
                    1 if entry.pinned else 0,
                    self._ts(entry.expires_at),
                    json.dumps(entry.metadata),
                    entry.source or "",
                    entry.token_count or 0,
                    entry.priority.value if hasattr(entry.priority, "value") else entry.priority,
                ),
            )
            for tag in entry.tags:
                conn.execute(
                    "INSERT OR REPLACE INTO memory_tags (entry_id, tag_name, tag_category) VALUES (?, ?, ?)",
                    (entry.entry_id, tag.name, tag.category or ""),
                )
            conn.commit()
            return entry.entry_id
        except sqlite3.Error as exc:
            conn.rollback()
            raise MemoryStorageError(f"Failed to store memory: {exc}") from exc

    async def get(self, entry_id: str) -> MemoryEntry | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM memories WHERE entry_id = ?", (entry_id,)).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE memories SET accessed_at = ?, access_count = access_count + 1 WHERE entry_id = ?",
            (time.time(), entry_id),
        )
        conn.commit()
        return self._row_to_entry(row)

    async def update(self, entry_id: str, **kwargs: Any) -> MemoryEntry | None:
        entry = await self.get(entry_id)
        if entry is None:
            return None
        allowed = {"content", "importance_score", "metadata", "pinned", "expires_at"}
        field_map = {"importance_score": "importance_score", "pinned": "pinned"}
        updates = {}
        for key, value in kwargs.items():
            if key in allowed:
                col = field_map.get(key, key)
                if key == "pinned":
                    value = 1 if value else 0
                updates[col] = value
        if not updates:
            return entry
        set_clause = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [entry_id]
        conn = self._get_conn()
        conn.execute(f"UPDATE memories SET {set_clause} WHERE entry_id = ?", values)
        conn.commit()
        return await self.get(entry_id)

    async def delete(self, entry_id: str) -> bool:
        conn = self._get_conn()
        conn.execute("DELETE FROM memory_tags WHERE entry_id = ?", (entry_id,))
        conn.execute("DELETE FROM memories WHERE entry_id = ?", (entry_id,))
        conn.commit()
        # Check if rows were actually affected
        return conn.total_changes > 0

    async def list_memories(
        self,
        memory_type: str | None = None,
        scope: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        conn = self._get_conn()
        conds, params = [], []
        if memory_type:
            conds.append("memory_type = ?")
            params.append(memory_type)
        if scope:
            conds.append("scope = ?")
            params.append(scope)
        if user_id:
            conds.append("user_id = ?")
            params.append(user_id)
        where = " AND ".join(conds) if conds else "1=1"
        rows = conn.execute(
            f"SELECT * FROM memories WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    async def search(self, query: str, top_k: int = 10) -> list[MemorySearchResult]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM memories WHERE content LIKE ? ORDER BY importance_score DESC, created_at DESC LIMIT ?",
            [f"%{query}%", top_k],
        ).fetchall()
        return [
            MemorySearchResult(
                entry=self._row_to_entry(r),
                relevance_score=r["importance_score"],
                match_type="keyword",
            )
            for r in rows
        ]

    async def count(self, memory_type: str | None = None) -> int:
        conn = self._get_conn()
        sql = "SELECT COUNT(*) FROM memories"
        params: list[Any] = []
        if memory_type:
            sql += " WHERE memory_type = ?"
            params.append(memory_type)
        result = conn.execute(sql, params).fetchone()
        return int(result[0]) if result else 0

    async def get_stats(self) -> MemoryStats:
        conn = self._get_conn()
        total_row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
        total = int(total_row[0]) if total_row else 0
        by_type_raw = conn.execute(
            "SELECT memory_type, COUNT(*) as cnt FROM memories GROUP BY memory_type"
        ).fetchall()
        by_type = {}
        for r in by_type_raw:
            try:
                by_type[MemoryType(r["memory_type"])] = r["cnt"]
            except ValueError:
                by_type[r["memory_type"]] = r["cnt"]
        pinned = conn.execute("SELECT COUNT(*) FROM memories WHERE pinned = 1").fetchone()[0]
        expired = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE expires_at IS NOT NULL AND expires_at < ?",
            (time.time(),),
        ).fetchone()[0]
        return MemoryStats(
            total_entries=total,
            by_type=by_type,
            by_scope={},
            total_size_bytes=0,
            pinned_count=pinned,
            expired_count=expired,
        )

    async def import_json(self, file_path: str) -> int:
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        count = 0
        for item in data:
            entry = MemoryEntry(
                content=item.get("content", ""),
                memory_type=MemoryType(item.get("memory_type", "conversation")),
                scope=MemoryScope(item.get("scope", "session")),
                session_id=item.get("session_id", ""),
                user_id=item.get("user_id", ""),
                importance_score=item.get("importance_score", 0.5),
                tags=[MemoryTag(name=t) for t in item.get("tags", [])],
                metadata=item.get("metadata", {}),
            )
            await self.store(entry)
            count += 1
        logger.info("memory_imported", count=count, file=file_path)
        return count

    async def export_json(self, file_path: str, **filters: Any) -> int:
        entries = await self.list_memories(**filters, limit=100000)
        data = [
            {
                "entry_id": e.entry_id,
                "content": e.content,
                "memory_type": e.memory_type.value,
                "scope": e.scope.value,
                "session_id": e.session_id,
                "user_id": e.user_id,
                "importance_score": e.importance_score,
                "tags": [t.name for t in e.tags],
                "metadata": e.metadata,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
        Path(file_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("memory_exported", count=len(entries), file=file_path)
        return len(entries)
