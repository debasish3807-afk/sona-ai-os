"""Concrete typed memory stores — implementing MemoryStore ABCs."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)

_SCHEMA_SEMANTIC = """
CREATE TABLE IF NOT EXISTS semantic_memories (
    entry_id TEXT PRIMARY KEY, content TEXT NOT NULL, entity_type TEXT DEFAULT '',
    entity_name TEXT DEFAULT '', tags TEXT DEFAULT '[]', metadata TEXT DEFAULT '{}',
    importance REAL DEFAULT 0.5, created_at REAL NOT NULL, accessed_at REAL NOT NULL,
    access_count INTEGER DEFAULT 0
);"""

_SCHEMA_EPISODIC = """
CREATE TABLE IF NOT EXISTS episodic_memories (
    entry_id TEXT PRIMARY KEY, content TEXT NOT NULL, event_type TEXT DEFAULT '',
    location TEXT DEFAULT '', participants TEXT DEFAULT '[]',
    emotion TEXT DEFAULT '', tags TEXT DEFAULT '[]', metadata TEXT DEFAULT '{}',
    importance REAL DEFAULT 0.5, created_at REAL NOT NULL, accessed_at REAL NOT NULL,
    access_count INTEGER DEFAULT 0
);"""

_SCHEMA_KNOWLEDGE = """
CREATE TABLE IF NOT EXISTS knowledge_entries (
    entry_id TEXT PRIMARY KEY, content TEXT NOT NULL, domain TEXT DEFAULT '',
    source TEXT DEFAULT '', confidence REAL DEFAULT 0.5, tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}', created_at REAL NOT NULL, accessed_at REAL NOT NULL,
    access_count INTEGER DEFAULT 0
);"""

_SCHEMA_CONVERSATION = """
CREATE TABLE IF NOT EXISTS conversation_memories (
    entry_id TEXT PRIMARY KEY, content TEXT NOT NULL, session_id TEXT DEFAULT '',
    user_id TEXT DEFAULT '', role TEXT DEFAULT 'user', tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}', importance REAL DEFAULT 0.5,
    created_at REAL NOT NULL, accessed_at REAL NOT NULL, access_count INTEGER DEFAULT 0
);"""


def _conn(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ts() -> float:
    return time.time()


class ConcreteSemanticMemory:
    """SQLite-backed semantic memory for facts and concepts."""

    def __init__(self, db_path: str = "semantic_memory.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def initialize(self) -> None:
        self._conn = _conn(self._db_path)
        self._conn.executescript(_SCHEMA_SEMANTIC)

    def _get(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Not initialized")
        return self._conn

    async def store(
        self,
        content: str,
        entity_type: str = "",
        entity_name: str = "",
        tags: list[str] | None = None,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        eid = str(uuid.uuid4())
        now = _ts()
        self._get().execute(
            "INSERT INTO semantic_memories VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                content,
                entity_type,
                entity_name,
                json.dumps(tags or []),
                json.dumps(metadata or {}),
                importance,
                now,
                now,
                0,
            ),
        )
        self._get().commit()
        return eid

    async def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        rows = (
            self._get()
            .execute(
                "SELECT * FROM semantic_memories WHERE content LIKE ? ORDER BY importance DESC, created_at DESC LIMIT ?",
                [f"%{query}%", top_k],
            )
            .fetchall()
        )
        return [dict(r) for r in rows]

    async def count(self) -> int:
        row = self._get().execute("SELECT COUNT(*) as c FROM semantic_memories").fetchone()
        return row["c"] if row else 0


class ConcreteEpisodicMemory:
    """SQLite-backed episodic memory for events and experiences."""

    def __init__(self, db_path: str = "episodic_memory.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def initialize(self) -> None:
        self._conn = _conn(self._db_path)
        self._conn.executescript(_SCHEMA_EPISODIC)

    def _get(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Not initialized")
        return self._conn

    async def store(
        self,
        content: str,
        event_type: str = "",
        location: str = "",
        participants: list[str] | None = None,
        emotion: str = "",
        importance: float = 0.5,
    ) -> str:
        eid = str(uuid.uuid4())
        now = _ts()
        self._get().execute(
            "INSERT INTO episodic_memories VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                content,
                event_type,
                location,
                json.dumps(participants or []),
                emotion,
                json.dumps({}),
                json.dumps({}),
                importance,
                now,
                now,
                0,
            ),
        )
        self._get().commit()
        return eid

    async def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        rows = (
            self._get()
            .execute(
                "SELECT * FROM episodic_memories WHERE content LIKE ? ORDER BY importance DESC, created_at DESC LIMIT ?",
                [f"%{query}%", top_k],
            )
            .fetchall()
        )
        return [dict(r) for r in rows]

    async def count(self) -> int:
        row = self._get().execute("SELECT COUNT(*) as c FROM episodic_memories").fetchone()
        return row["c"] if row else 0


class ConcreteKnowledgeMemory:
    """SQLite-backed knowledge memory for documents and facts."""

    def __init__(self, db_path: str = "knowledge_memory.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def initialize(self) -> None:
        self._conn = _conn(self._db_path)
        self._conn.executescript(_SCHEMA_KNOWLEDGE)

    def _get(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Not initialized")
        return self._conn

    async def store(
        self, content: str, domain: str = "", source: str = "", confidence: float = 0.5
    ) -> str:
        eid = str(uuid.uuid4())
        now = _ts()
        self._get().execute(
            "INSERT INTO knowledge_entries VALUES (?,?,?,?,?,?,?,?,?,?)",
            (eid, content, domain, source, confidence, json.dumps([]), json.dumps({}), now, now, 0),
        )
        self._get().commit()
        return eid

    async def search(
        self, query: str, domain: str | None = None, top_k: int = 10
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM knowledge_entries WHERE content LIKE ?"
        params: list[Any] = [f"%{query}%"]
        if domain:
            sql += " AND domain = ?"
            params.append(domain)
        sql += " ORDER BY confidence DESC, created_at DESC LIMIT ?"
        params.append(top_k)
        rows = self._get().execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    async def count(self) -> int:
        row = self._get().execute("SELECT COUNT(*) as c FROM knowledge_entries").fetchone()
        return row["c"] if row else 0


class ConcreteConversationMemory:
    """SQLite-backed conversation memory for dialogue history."""

    def __init__(self, db_path: str = "conversation_memory.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def initialize(self) -> None:
        self._conn = _conn(self._db_path)
        self._conn.executescript(_SCHEMA_CONVERSATION)

    def _get(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Not initialized")
        return self._conn

    async def store(
        self, content: str, session_id: str = "", user_id: str = "", role: str = "user"
    ) -> str:
        eid = str(uuid.uuid4())
        now = _ts()
        self._get().execute(
            "INSERT INTO conversation_memories VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                content,
                session_id,
                user_id,
                role,
                json.dumps([]),
                json.dumps({}),
                0.5,
                now,
                now,
                0,
            ),
        )
        self._get().commit()
        return eid

    async def get_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = (
            self._get()
            .execute(
                "SELECT * FROM conversation_memories WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
                [session_id, limit],
            )
            .fetchall()
        )
        return [dict(r) for r in rows]

    async def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        rows = (
            self._get()
            .execute(
                "SELECT * FROM conversation_memories WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
                [f"%{query}%", top_k],
            )
            .fetchall()
        )
        return [dict(r) for r in rows]

    async def count(self) -> int:
        row = self._get().execute("SELECT COUNT(*) as c FROM conversation_memories").fetchone()
        return row["c"] if row else 0
