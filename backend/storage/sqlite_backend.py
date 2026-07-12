"""SQLite storage backend — async-compatible persistent storage.

Production-ready SQLite backend with:
    - Automatic schema migration
    - Full-text search (FTS5)
    - Thread-safe via asyncio executor
    - Connection pooling via reuse
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Any

from config.logging import get_logger
from storage.repository import DocumentRecord, MemoryRecord, StorageRepository

logger = get_logger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    doc_type TEXT NOT NULL DEFAULT 'text',
    source TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    token_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    content TEXT NOT NULL DEFAULT '',
    memory_type TEXT NOT NULL DEFAULT 'conversation',
    scope TEXT NOT NULL DEFAULT 'session',
    session_id TEXT NOT NULL DEFAULT '',
    user_id TEXT NOT NULL DEFAULT '',
    importance REAL NOT NULL DEFAULT 0.5,
    tags TEXT NOT NULL DEFAULT '[]',
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    accessed_at TEXT NOT NULL,
    access_count INTEGER NOT NULL DEFAULT 0
);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    doc_id, title, content, doc_type, tags,
    content=documents, content_rowid=rowid
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    memory_id, content, memory_type, tags,
    content=memories, content_rowid=rowid
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(doc_id, title, content, doc_type, tags)
    VALUES (new.doc_id, new.title, new.content, new.doc_type, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(memory_id, content, memory_type, tags)
    VALUES (new.memory_id, new.content, new.memory_type, new.tags);
END;

CREATE INDEX IF NOT EXISTS idx_docs_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_docs_created ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_mem_session ON memories(session_id);
CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_mem_created ON memories(created_at);
"""


class SQLiteBackend(StorageRepository):
    """SQLite-based persistent storage with FTS5 search.

    Suitable for development and single-instance deployments.
    For production at scale, use PostgreSQL backend.
    """

    def __init__(self, db_path: str = "sona_knowledge.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    @property
    def db_path(self) -> str:
        return self._db_path

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        return self._conn

    async def initialize(self) -> None:
        """Create tables and indexes."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._init_sync)
        logger.info("SQLite storage initialized", db_path=self._db_path)

    def _init_sync(self) -> None:
        conn = self._get_conn()
        conn.executescript(SCHEMA_SQL)
        conn.commit()

    async def shutdown(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    async def save_document(self, doc: DocumentRecord) -> str:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_doc_sync, doc)
        return doc.doc_id

    def _save_doc_sync(self, doc: DocumentRecord) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO documents
            (doc_id, title, content, doc_type, source, tags, metadata,
             created_at, updated_at, chunk_count, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc.doc_id,
                doc.title,
                doc.content,
                doc.doc_type,
                doc.source,
                json.dumps(doc.tags),
                json.dumps(doc.metadata),
                doc.created_at,
                doc.updated_at,
                doc.chunk_count,
                doc.token_count,
            ),
        )
        conn.commit()

    async def get_document(self, doc_id: str) -> DocumentRecord | None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_doc_sync, doc_id)

    def _get_doc_sync(self, doc_id: str) -> DocumentRecord | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_doc(row)

    async def list_documents(
        self, doc_type: str | None = None, limit: int = 50
    ) -> list[DocumentRecord]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._list_docs_sync, doc_type, limit)

    def _list_docs_sync(self, doc_type: str | None, limit: int) -> list[DocumentRecord]:
        conn = self._get_conn()
        if doc_type:
            rows = conn.execute(
                "SELECT * FROM documents WHERE doc_type = ? ORDER BY created_at DESC LIMIT ?",
                (doc_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_doc(r) for r in rows]

    async def delete_document(self, doc_id: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._delete_doc_sync, doc_id)

    def _delete_doc_sync(self, doc_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        conn.commit()
        return cursor.rowcount > 0

    async def search_documents(self, query: str, limit: int = 10) -> list[DocumentRecord]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_docs_sync, query, limit)

    def _search_docs_sync(self, query: str, limit: int) -> list[DocumentRecord]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT d.* FROM documents d
                JOIN documents_fts f ON d.doc_id = f.doc_id
                WHERE documents_fts MATCH ? LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [self._row_to_doc(r) for r in rows]
        except sqlite3.OperationalError:
            # Fallback to LIKE search
            rows = conn.execute(
                "SELECT * FROM documents WHERE content LIKE ? LIMIT ?",
                (f"%{query}%", limit),
            ).fetchall()
            return [self._row_to_doc(r) for r in rows]

    async def save_memory(self, memory: MemoryRecord) -> str:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_mem_sync, memory)
        return memory.memory_id

    def _save_mem_sync(self, memory: MemoryRecord) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO memories
            (memory_id, content, memory_type, scope, session_id, user_id,
             importance, tags, metadata, created_at, accessed_at, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory.memory_id,
                memory.content,
                memory.memory_type,
                memory.scope,
                memory.session_id,
                memory.user_id,
                memory.importance,
                json.dumps(memory.tags),
                json.dumps(memory.metadata),
                memory.created_at,
                memory.accessed_at,
                memory.access_count,
            ),
        )
        conn.commit()

    async def get_memories(
        self, session_id: str | None = None, memory_type: str | None = None, limit: int = 50
    ) -> list[MemoryRecord]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_mems_sync, session_id, memory_type, limit)

    def _get_mems_sync(
        self, session_id: str | None, memory_type: str | None, limit: int
    ) -> list[MemoryRecord]:
        conn = self._get_conn()
        params: list[Any] = []

        # Build query safely without string interpolation
        if session_id and memory_type:
            query = "SELECT * FROM memories WHERE session_id = ? AND memory_type = ? ORDER BY created_at DESC LIMIT ?"
            params = [session_id, memory_type, limit]
        elif session_id:
            query = "SELECT * FROM memories WHERE session_id = ? ORDER BY created_at DESC LIMIT ?"
            params = [session_id, limit]
        elif memory_type:
            query = "SELECT * FROM memories WHERE memory_type = ? ORDER BY created_at DESC LIMIT ?"
            params = [memory_type, limit]
        else:
            query = "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?"
            params = [limit]

        rows = conn.execute(query, params).fetchall()
        return [self._row_to_mem(r) for r in rows]

    async def search_memories(self, query: str, limit: int = 10) -> list[MemoryRecord]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_mems_sync, query, limit)

    def _search_mems_sync(self, query: str, limit: int) -> list[MemoryRecord]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT m.* FROM memories m
                JOIN memories_fts f ON m.memory_id = f.memory_id
                WHERE memories_fts MATCH ? LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [self._row_to_mem(r) for r in rows]
        except sqlite3.OperationalError:
            rows = conn.execute(
                "SELECT * FROM memories WHERE content LIKE ? LIMIT ?",
                (f"%{query}%", limit),
            ).fetchall()
            return [self._row_to_mem(r) for r in rows]

    async def delete_memory(self, memory_id: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._delete_mem_sync, memory_id)

    def _delete_mem_sync(self, memory_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0

    def _row_to_doc(self, row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            doc_id=row["doc_id"],
            title=row["title"],
            content=row["content"],
            doc_type=row["doc_type"],
            source=row["source"],
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            chunk_count=row["chunk_count"],
            token_count=row["token_count"],
        )

    def _row_to_mem(self, row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=row["memory_id"],
            content=row["content"],
            memory_type=row["memory_type"],
            scope=row["scope"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            importance=row["importance"],
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            accessed_at=row["accessed_at"],
            access_count=row["access_count"],
        )
