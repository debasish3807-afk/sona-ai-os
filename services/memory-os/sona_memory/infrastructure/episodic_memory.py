"""Episodic memory manager.

Stores event-based memories with temporal context, supporting
time-range queries and linked episode relationships.
"""

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime

from sona_memory.domain.models import MemoryEntry, MemoryType


@dataclass
class EpisodicConfig:
    """Configuration for episodic memory."""

    max_capacity_per_user: int = 5000
    default_importance: float = 0.6


class EpisodicMemory:
    """Event-based memory with temporal indexing.

    Stores episodes indexed by time, supporting time-range queries
    and linked episode relationships through metadata.
    """

    def __init__(self, config: EpisodicConfig | None = None) -> None:
        self._config = config or EpisodicConfig()
        # user_id -> list of entries sorted by created_at
        self._store: dict[str, list[MemoryEntry]] = {}
        self._lock = asyncio.Lock()

    @property
    def config(self) -> EpisodicConfig:
        """Current configuration."""
        return self._config

    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store an episodic memory entry.

        Entries are kept sorted by creation time.
        """
        async with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []

            # Ensure memory type
            if entry.memory_type != MemoryType.EPISODIC:
                entry = replace(entry, memory_type=MemoryType.EPISODIC)

            # Set default importance if not specified
            if entry.importance == 0.5:
                entry = replace(entry, importance=self._config.default_importance)

            self._store[user_id].append(entry)
            # Sort by created_at (None goes to the start)
            self._store[user_id].sort(key=lambda e: e.created_at.timestamp() if e.created_at else 0)

            # Evict oldest if over capacity
            while len(self._store[user_id]) > self._config.max_capacity_per_user:
                self._store[user_id].pop(0)

            return entry.id

    async def get(self, user_id: str, memory_id: str) -> MemoryEntry | None:
        """Get a specific episodic memory by ID."""
        async with self._lock:
            if user_id not in self._store:
                return None
            for entry in self._store[user_id]:
                if entry.id == memory_id:
                    return entry
            return None

    async def get_by_time_range(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[MemoryEntry]:
        """Get episodes within a time range."""
        async with self._lock:
            if user_id not in self._store:
                return []

            start_ts = start.timestamp()
            end_ts = end.timestamp()

            return [
                entry
                for entry in self._store[user_id]
                if entry.created_at is not None
                and start_ts <= entry.created_at.timestamp() <= end_ts
            ]

    async def get_related(self, user_id: str, episode_id: str) -> list[MemoryEntry]:
        """Get episodes related to a given episode via metadata links."""
        async with self._lock:
            if user_id not in self._store:
                return []

            # Find the source episode
            source = None
            for entry in self._store[user_id]:
                if entry.id == episode_id:
                    source = entry
                    break

            if source is None:
                return []

            # Get related IDs from metadata
            related_ids: set[str] = set()
            if source.metadata and "related_episodes" in source.metadata:
                related_ids.update(source.metadata["related_episodes"])

            # Also find entries that link back to this episode
            for entry in self._store[user_id]:
                if entry.metadata and "related_episodes" in entry.metadata:
                    if episode_id in entry.metadata["related_episodes"]:
                        related_ids.add(entry.id)

            return [
                entry
                for entry in self._store[user_id]
                if entry.id in related_ids and entry.id != episode_id
            ]

    async def get_recent(self, user_id: str, limit: int = 10) -> list[MemoryEntry]:
        """Get the most recent episodes."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return list(reversed(self._store[user_id][-limit:]))

    async def get_by_tags(self, user_id: str, tags: set[str]) -> list[MemoryEntry]:
        """Get episodes matching any of the given tags."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return [entry for entry in self._store[user_id] if set(entry.tags) & tags]

    async def get_all(self, user_id: str) -> list[MemoryEntry]:
        """Get all episodic memories for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return list(self._store[user_id])

    async def remove(self, user_id: str, memory_id: str) -> bool:
        """Remove a specific episode."""
        async with self._lock:
            if user_id not in self._store:
                return False
            initial_len = len(self._store[user_id])
            self._store[user_id] = [e for e in self._store[user_id] if e.id != memory_id]
            return len(self._store[user_id]) < initial_len

    async def count(self, user_id: str) -> int:
        """Get the number of episodes for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            return len(self._store[user_id])

    async def clear(self, user_id: str) -> int:
        """Clear all episodic memory for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            count = len(self._store[user_id])
            self._store[user_id].clear()
            return count
