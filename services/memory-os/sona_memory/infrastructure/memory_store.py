"""In-memory store implementation of MemoryStorePort.

Provides a full in-memory implementation for local development,
testing, and as a reference for production adapters.
"""

import asyncio
import uuid
from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime

from sona_memory.application.ports import MemoryStorePort
from sona_memory.domain.models import MemoryEntry, MemoryQuery, MemoryType


class InMemoryStore(MemoryStorePort):
    """Full in-memory implementation of MemoryStorePort.

    Uses a dict[str, list[MemoryEntry]] for per-user storage
    with filtering, ranking, and consolidation support.
    """

    def __init__(self) -> None:
        # user_id -> list of entries
        self._store: dict[str, list[MemoryEntry]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store a memory entry, generating UUID if needed."""
        async with self._lock:
            # Generate ID if empty
            memory_id = entry.id if entry.id else str(uuid.uuid4())
            if entry.id != memory_id:
                entry = replace(entry, id=memory_id)

            # Set created_at if not present
            if entry.created_at is None:
                entry = replace(entry, created_at=datetime.now(UTC))

            self._store[user_id].append(entry)
            return memory_id

    async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
        """Retrieve memories matching query criteria.

        Filters by type, importance, and time_range, then returns
        top_k results sorted by importance (descending).
        """
        async with self._lock:
            entries = list(self._store.get(query.user_id, []))

        # Filter by memory types
        if query.memory_types:
            entries = [e for e in entries if e.memory_type in query.memory_types]

        # Filter by minimum importance
        if query.min_importance > 0:
            entries = [e for e in entries if e.importance >= query.min_importance]

        # Filter by time range
        if query.time_range:
            start, end = query.time_range
            entries = [
                e for e in entries if e.created_at is not None and start <= e.created_at <= end
            ]

        # Filter expired
        now = datetime.now(UTC)
        entries = [e for e in entries if e.expires_at is None or e.expires_at > now]

        # Sort by importance descending
        entries.sort(key=lambda e: e.importance, reverse=True)

        return entries[: query.top_k]

    async def consolidate(self, user_id: str) -> int:
        """Promote important short-term memories to long-term.

        Memories with importance >= 0.7 are promoted from SHORT_TERM
        to LONG_TERM with their expiration removed.
        """
        async with self._lock:
            if user_id not in self._store:
                return 0

            consolidated_count = 0
            new_entries: list[MemoryEntry] = []

            for entry in self._store[user_id]:
                if entry.memory_type == MemoryType.SHORT_TERM and entry.importance >= 0.7:
                    # Promote to long-term
                    promoted = replace(
                        entry,
                        memory_type=MemoryType.LONG_TERM,
                        expires_at=None,
                    )
                    new_entries.append(promoted)
                    consolidated_count += 1
                else:
                    new_entries.append(entry)

            self._store[user_id] = new_entries
            return consolidated_count

    async def forget(self, user_id: str, memory_id: str) -> bool:
        """Remove a specific memory entry."""
        async with self._lock:
            if user_id not in self._store:
                return False
            initial_len = len(self._store[user_id])
            self._store[user_id] = [e for e in self._store[user_id] if e.id != memory_id]
            return len(self._store[user_id]) < initial_len

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> list[MemoryEntry]:
        """Get conversation history for a session from working memory.

        Filters by session_id in metadata across all users.
        """
        async with self._lock:
            results: list[MemoryEntry] = []
            for entries in self._store.values():
                for entry in entries:
                    if entry.memory_type != MemoryType.WORKING:
                        continue
                    if entry.metadata and entry.metadata.get("session_id") == session_id:
                        results.append(entry)

            # Sort by created_at
            results.sort(key=lambda e: e.created_at.timestamp() if e.created_at else 0)
            return results[-limit:]

    async def get_all(self, user_id: str) -> list[MemoryEntry]:
        """Get all entries for a user (utility method)."""
        async with self._lock:
            return list(self._store.get(user_id, []))

    async def count(self, user_id: str) -> int:
        """Get entry count for a user."""
        async with self._lock:
            return len(self._store.get(user_id, []))
