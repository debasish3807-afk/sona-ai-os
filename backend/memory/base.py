"""Abstract memory store interface.

This module defines the core MemoryStore abstract base class which all
memory storage backends must implement. It provides a comprehensive
interface covering CRUD operations, search, lifecycle management,
tagging, pinning, and import/export capabilities.

Classes:
    MemoryStore: The core abstract interface for all memory backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .types import (
    MemoryEntry,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryStats,
    MemoryTag,
    MemoryType,
)


class MemoryStore(ABC):
    """The core abstract interface for all memory storage backends.

    MemoryStore defines the contract that all memory backend implementations
    must fulfill. It provides a comprehensive set of async operations covering
    the full memory lifecycle: creation, retrieval, modification, deletion,
    search, tagging, pinning, and bulk import/export.

    Implementations may target different backends (in-memory, SQLite, PostgreSQL,
    Redis, vector databases, etc.) while maintaining a consistent API.

    All I/O operations are async to support high-concurrency workloads
    without blocking the event loop.
    """

    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str:
        """Store a new memory entry.

        Persists the given entry to the storage backend and returns
        its assigned entry ID.

        Args:
            entry: The memory entry to store.

        Returns:
            The entry_id of the stored memory.

        Raises:
            MemoryStorageError: If the store operation fails.
            MemoryCapacityError: If storage capacity is exceeded.
        """
        ...

    @abstractmethod
    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve a single memory entry by its ID.

        Args:
            entry_id: The unique identifier of the entry to retrieve.

        Returns:
            The memory entry if found, None otherwise.

        Raises:
            MemoryRetrievalError: If the retrieval operation fails.
        """
        ...

    @abstractmethod
    async def update(self, entry_id: str, **kwargs: Any) -> MemoryEntry | None:
        """Update fields of an existing memory entry.

        Only the specified keyword arguments are updated; unspecified
        fields remain unchanged.

        Args:
            entry_id: The ID of the entry to update.
            **kwargs: Fields to update with their new values.

        Returns:
            The updated memory entry, or None if entry not found.

        Raises:
            MemoryStorageError: If the update operation fails.
        """
        ...

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry permanently.

        Args:
            entry_id: The ID of the entry to delete.

        Returns:
            True if the entry was found and deleted, False otherwise.

        Raises:
            MemoryStorageError: If the delete operation fails.
        """
        ...

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search for memory entries matching the given query.

        Executes a search using the configured retrieval strategy
        (semantic, keyword, hybrid, etc.) and returns ranked results.

        Args:
            query: The search query parameters.

        Returns:
            List of matching results with relevance scores.

        Raises:
            MemoryRetrievalError: If the search operation fails.
        """
        ...

    @abstractmethod
    async def list_entries(
        self,
        memory_type: MemoryType | None = None,
        scope: MemoryScope | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        """List memory entries with optional filtering and pagination.

        Args:
            memory_type: Optional filter by memory type.
            scope: Optional filter by scope.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip for pagination.

        Returns:
            List of memory entries matching the filters.
        """
        ...

    @abstractmethod
    async def count(
        self,
        memory_type: MemoryType | None = None,
        scope: MemoryScope | None = None,
    ) -> int:
        """Count memory entries with optional filtering.

        Args:
            memory_type: Optional filter by memory type.
            scope: Optional filter by scope.

        Returns:
            Number of entries matching the filters.
        """
        ...

    @abstractmethod
    async def clear(
        self,
        memory_type: MemoryType | None = None,
        scope: MemoryScope | None = None,
    ) -> int:
        """Clear (delete) all entries matching the given filters.

        If no filters are specified, ALL entries are cleared.

        Args:
            memory_type: Optional filter to clear only specific types.
            scope: Optional filter to clear only specific scopes.

        Returns:
            Number of entries that were cleared/deleted.

        Raises:
            MemoryStorageError: If the clear operation fails.
        """
        ...

    @abstractmethod
    async def pin(self, entry_id: str) -> bool:
        """Pin a memory entry to prevent eviction.

        Pinned entries are exempt from capacity-based eviction and
        retention policy expiration.

        Args:
            entry_id: The ID of the entry to pin.

        Returns:
            True if the entry was found and pinned, False otherwise.

        Raises:
            MemoryPolicyViolation: If pinning violates pin policy limits.
        """
        ...

    @abstractmethod
    async def unpin(self, entry_id: str) -> bool:
        """Unpin a memory entry, making it eligible for eviction again.

        Args:
            entry_id: The ID of the entry to unpin.

        Returns:
            True if the entry was found and unpinned, False otherwise.
        """
        ...

    @abstractmethod
    async def tag(self, entry_id: str, tags: list[MemoryTag]) -> bool:
        """Add tags to a memory entry.

        Args:
            entry_id: The ID of the entry to tag.
            tags: List of tags to add to the entry.

        Returns:
            True if the entry was found and tags were added, False otherwise.
        """
        ...

    @abstractmethod
    async def untag(self, entry_id: str, tag_names: list[str]) -> bool:
        """Remove tags from a memory entry by tag name.

        Args:
            entry_id: The ID of the entry to untag.
            tag_names: List of tag names to remove from the entry.

        Returns:
            True if the entry was found and tags were removed, False otherwise.
        """
        ...

    @abstractmethod
    async def get_stats(self) -> MemoryStats:
        """Get aggregate statistics for this memory store.

        Returns:
            Statistics including entry counts, size, and temporal bounds.
        """
        ...

    @abstractmethod
    async def export_entries(
        self,
        memory_type: MemoryType | None = None,
        scope: MemoryScope | None = None,
    ) -> list[dict[str, Any]]:
        """Export entries as serialized dictionaries for backup/transfer.

        Args:
            memory_type: Optional filter to export only specific types.
            scope: Optional filter to export only specific scopes.

        Returns:
            List of serialized entry dictionaries.

        Raises:
            MemoryImportExportError: If the export operation fails.
        """
        ...

    @abstractmethod
    async def import_entries(self, entries: list[dict[str, Any]]) -> int:
        """Import entries from serialized dictionaries.

        Args:
            entries: List of serialized entry dictionaries to import.

        Returns:
            Number of entries successfully imported.

        Raises:
            MemoryImportExportError: If the import operation fails.
        """
        ...

    @abstractmethod
    async def health(self) -> bool:
        """Check if this memory store is healthy and operational.

        Returns:
            True if the store is operational, False otherwise.
        """
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the memory store (create tables, connect to backends, etc.).

        This must be called before any other operations. Implementations
        should be idempotent (safe to call multiple times).

        Raises:
            MemoryStorageError: If initialization fails.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shut down the memory store.

        Flushes pending writes, closes connections, and releases resources.
        After shutdown, no other operations should be called.
        """
        ...
