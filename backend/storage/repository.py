"""Storage repository — abstract interface for persistent data.

Defines the contract for document and memory persistence backends.
Implementations can use SQLite, PostgreSQL, Redis, or any combination.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass
class DocumentRecord:
    """A stored document with metadata."""

    doc_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    content: str = ""
    doc_type: str = "text"  # text, code, markdown, pdf, etc.
    source: str = ""  # file path, URL, etc.
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    chunk_count: int = 0
    token_count: int = 0


@dataclass
class MemoryRecord:
    """A stored memory entry with metadata."""

    memory_id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    memory_type: str = "conversation"
    scope: str = "session"
    session_id: str = ""
    user_id: str = ""
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    access_count: int = 0


class StorageRepository(ABC):
    """Abstract repository for persistent storage operations."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize storage (create tables, connections)."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Close connections and release resources."""
        ...

    # --- Document Operations ---

    @abstractmethod
    async def save_document(self, doc: DocumentRecord) -> str:
        """Save a document. Returns doc_id."""
        ...

    @abstractmethod
    async def get_document(self, doc_id: str) -> DocumentRecord | None:
        """Retrieve a document by ID."""
        ...

    @abstractmethod
    async def list_documents(
        self, doc_type: str | None = None, limit: int = 50
    ) -> list[DocumentRecord]:
        """List documents with optional type filter."""
        ...

    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document. Returns True if found and deleted."""
        ...

    @abstractmethod
    async def search_documents(self, query: str, limit: int = 10) -> list[DocumentRecord]:
        """Full-text search across documents."""
        ...

    # --- Memory Operations ---

    @abstractmethod
    async def save_memory(self, memory: MemoryRecord) -> str:
        """Save a memory record. Returns memory_id."""
        ...

    @abstractmethod
    async def get_memories(
        self,
        session_id: str | None = None,
        memory_type: str | None = None,
        limit: int = 50,
    ) -> list[MemoryRecord]:
        """Retrieve memories with filters."""
        ...

    @abstractmethod
    async def search_memories(self, query: str, limit: int = 10) -> list[MemoryRecord]:
        """Full-text search across memories."""
        ...

    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory record."""
        ...
