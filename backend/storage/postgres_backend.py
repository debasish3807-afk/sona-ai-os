"""PostgreSQL storage backend — async persistent storage.

Production-ready PostgreSQL backend using asyncpg with:
    - Connection pooling
    - Full-text search (tsvector + GIN index)
    - Automatic schema migration
    - JSON metadata storage
    - Graceful fallback to SQLite if PostgreSQL unavailable

Requires: asyncpg (pip install asyncpg)
Configure via DATABASE_URL env var:
    postgresql://user:pass@localhost:5432/sona_db
"""

from __future__ import annotations

import json
import os
from typing import Any

from config.logging import get_logger
from storage.repository import DocumentRecord, MemoryRecord, StorageRepository

logger = get_logger(__name__)

DEFAULT_DATABASE_URL = "postgresql://sona:sona@localhost:5432/sona_db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    doc_type TEXT NOT NULL DEFAULT 'text',
    source TEXT NOT NULL DEFAULT '',
    tags JSONB NOT NULL DEFAULT '[]',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT '',
    chunk_count INTEGER NOT NULL DEFAULT 0,
    token_count INTEGER NOT NULL DEFAULT 0,
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
    ) STORED
);

CREATE INDEX IF NOT EXISTS idx_documents_search ON documents USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents (doc_type);

CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    content TEXT NOT NULL DEFAULT '',
    memory_type TEXT NOT NULL DEFAULT 'conversation',
    scope TEXT NOT NULL DEFAULT 'session',
    session_id TEXT NOT NULL DEFAULT '',
    user_id TEXT NOT NULL DEFAULT '',
    importance REAL NOT NULL DEFAULT 0.5,
    tags JSONB NOT NULL DEFAULT '[]',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT '',
    accessed_at TEXT NOT NULL DEFAULT '',
    access_count INTEGER NOT NULL DEFAULT 0,
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(content, ''))
    ) STORED
);

CREATE INDEX IF NOT EXISTS idx_memories_search ON memories USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_memories_session ON memories (session_id);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories (memory_type);
"""


class PostgresBackend(StorageRepository):
    """PostgreSQL storage backend with connection pooling and full-text search.

    Falls back gracefully if asyncpg is not installed or PostgreSQL
    is not available.
    """

    def __init__(self, database_url: str | None = None) -> None:
        self._database_url = database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
        self._pool: Any = None
        self._available = False

    async def initialize(self) -> None:
        """Create connection pool and run migrations."""
        try:
            import asyncpg  # noqa: F401 — runtime import for optional dep

            self._pool = await asyncpg.create_pool(
                self._database_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            # Run schema migrations
            async with self._pool.acquire() as conn:
                await conn.execute(SCHEMA_SQL)
            self._available = True
            logger.info("postgres_initialized", url=self._database_url.split("@")[-1])
        except ImportError:
            logger.warning("asyncpg_not_installed", hint="pip install asyncpg")
            self._available = False
        except Exception as exc:
            logger.warning("postgres_unavailable", error=str(exc))
            self._available = False

    async def shutdown(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
        self._available = False
        logger.info("postgres_shutdown")

    @property
    def is_available(self) -> bool:
        """Whether PostgreSQL is connected and operational."""
        return self._available

    # --- Document Operations ---

    async def save_document(self, doc: DocumentRecord) -> str:
        """Save document using UPSERT."""
        if not self._available:
            return doc.doc_id
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO documents (
                    doc_id, title, content, doc_type, source,
                    tags, metadata, created_at, updated_at,
                    chunk_count, token_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (doc_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    doc_type = EXCLUDED.doc_type,
                    source = EXCLUDED.source,
                    tags = EXCLUDED.tags,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at,
                    chunk_count = EXCLUDED.chunk_count,
                    token_count = EXCLUDED.token_count
                """,
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
            )
        return doc.doc_id

    async def get_document(self, doc_id: str) -> DocumentRecord | None:
        """Retrieve document by ID."""
        if not self._available:
            return None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM documents WHERE doc_id = $1", doc_id)
        if not row:
            return None
        return self._row_to_document(row)

    async def list_documents(
        self, doc_type: str | None = None, limit: int = 50
    ) -> list[DocumentRecord]:
        """List documents with optional type filter."""
        if not self._available:
            return []
        async with self._pool.acquire() as conn:
            if doc_type:
                rows = await conn.fetch(
                    "SELECT * FROM documents WHERE doc_type = $1 ORDER BY created_at DESC LIMIT $2",
                    doc_type,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM documents ORDER BY created_at DESC LIMIT $1",
                    limit,
                )
        return [self._row_to_document(r) for r in rows]

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if not self._available:
            return False
        async with self._pool.acquire() as conn:
            result = await conn.execute("DELETE FROM documents WHERE doc_id = $1", doc_id)
        return str(result) == "DELETE 1"

    async def search_documents(self, query: str, limit: int = 10) -> list[DocumentRecord]:
        """Full-text search across documents using tsvector."""
        if not self._available:
            return []
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT *, ts_rank(search_vector, plainto_tsquery('english', $1)) AS rank
                FROM documents
                WHERE search_vector @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT $2
                """,
                query,
                limit,
            )
        return [self._row_to_document(r) for r in rows]

    # --- Memory Operations ---

    async def save_memory(self, memory: MemoryRecord) -> str:
        """Save memory using UPSERT."""
        if not self._available:
            return memory.memory_id
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO memories (
                    memory_id, content, memory_type, scope,
                    session_id, user_id, importance, tags, metadata,
                    created_at, accessed_at, access_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (memory_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    importance = EXCLUDED.importance,
                    tags = EXCLUDED.tags,
                    metadata = EXCLUDED.metadata,
                    accessed_at = EXCLUDED.accessed_at,
                    access_count = EXCLUDED.access_count
                """,
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
            )
        return memory.memory_id

    async def get_memories(
        self,
        session_id: str | None = None,
        memory_type: str | None = None,
        limit: int = 50,
    ) -> list[MemoryRecord]:
        """Retrieve memories with filters."""
        if not self._available:
            return []
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if session_id:
            conditions.append(f"session_id = ${idx}")
            params.append(session_id)
            idx += 1
        if memory_type:
            conditions.append(f"memory_type = ${idx}")
            params.append(memory_type)
            idx += 1

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        query = (
            f"SELECT * FROM memories {where}"  # nosec B608
            f" ORDER BY created_at DESC LIMIT ${idx}"
        )

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._row_to_memory(r) for r in rows]

    async def search_memories(self, query: str, limit: int = 10) -> list[MemoryRecord]:
        """Full-text search across memories using tsvector."""
        if not self._available:
            return []
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT *, ts_rank(search_vector, plainto_tsquery('english', $1)) AS rank
                FROM memories
                WHERE search_vector @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT $2
                """,
                query,
                limit,
            )
        return [self._row_to_memory(r) for r in rows]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory record."""
        if not self._available:
            return False
        async with self._pool.acquire() as conn:
            result = await conn.execute("DELETE FROM memories WHERE memory_id = $1", memory_id)
        return str(result) == "DELETE 1"

    # --- Helpers ---

    @staticmethod
    def _row_to_document(row: Any) -> DocumentRecord:
        """Convert a database row to DocumentRecord."""
        tags = row["tags"]
        if isinstance(tags, str):
            tags = json.loads(tags)
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        return DocumentRecord(
            doc_id=row["doc_id"],
            title=row["title"],
            content=row["content"],
            doc_type=row["doc_type"],
            source=row["source"],
            tags=tags if isinstance(tags, list) else [],
            metadata=metadata if isinstance(metadata, dict) else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            chunk_count=row["chunk_count"],
            token_count=row["token_count"],
        )

    @staticmethod
    def _row_to_memory(row: Any) -> MemoryRecord:
        """Convert a database row to MemoryRecord."""
        tags = row["tags"]
        if isinstance(tags, str):
            tags = json.loads(tags)
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        return MemoryRecord(
            memory_id=row["memory_id"],
            content=row["content"],
            memory_type=row["memory_type"],
            scope=row["scope"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            importance=row["importance"],
            tags=tags if isinstance(tags, list) else [],
            metadata=metadata if isinstance(metadata, dict) else {},
            created_at=row["created_at"],
            accessed_at=row["accessed_at"],
            access_count=row["access_count"],
        )
