"""Short-term memory manager.

Medium-capacity memory with importance-based eviction and TTL expiration.
Candidates for consolidation to long-term memory.
"""

import asyncio
import time
from dataclasses import dataclass, replace

from sona_memory.domain.models import MemoryEntry, MemoryType


@dataclass
class ShortTermConfig:
    """Configuration for short-term memory."""

    max_capacity: int = 1000
    ttl_seconds: int = 86400  # 24 hours
    consolidation_threshold: float = 0.7  # min importance for promotion


class ShortTermMemory:
    """Medium-capacity short-term memory with importance-based eviction.

    Entries are stored with TTL-based expiration. When capacity is exceeded,
    the least important entries are evicted first.
    """

    def __init__(self, config: ShortTermConfig | None = None) -> None:
        self._config = config or ShortTermConfig()
        # user_id -> list of (entry, insert_time)
        self._store: dict[str, list[tuple[MemoryEntry, float]]] = {}
        self._lock = asyncio.Lock()

    @property
    def config(self) -> ShortTermConfig:
        """Current configuration."""
        return self._config

    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store an entry in short-term memory.

        Evicts least important entries when capacity is exceeded.
        """
        async with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []

            now = time.time()
            self._evict_expired(user_id, now)

            # Evict least important if at capacity
            while len(self._store[user_id]) >= self._config.max_capacity:
                self._evict_least_important(user_id)

            # Ensure memory type is SHORT_TERM
            if entry.memory_type != MemoryType.SHORT_TERM:
                entry = replace(entry, memory_type=MemoryType.SHORT_TERM)

            self._store[user_id].append((entry, now))
            return entry.id

    async def get(self, user_id: str, memory_id: str) -> MemoryEntry | None:
        """Get a specific entry by ID."""
        async with self._lock:
            if user_id not in self._store:
                return None
            now = time.time()
            for entry, insert_time in self._store[user_id]:
                if entry.id == memory_id:
                    if (now - insert_time) > self._config.ttl_seconds:
                        return None
                    return entry
            return None

    async def get_all(self, user_id: str) -> list[MemoryEntry]:
        """Get all non-expired entries for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            now = time.time()
            self._evict_expired(user_id, now)
            return [entry for entry, _ in self._store[user_id]]

    async def get_consolidation_candidates(self, user_id: str) -> list[MemoryEntry]:
        """Get entries eligible for promotion to long-term memory.

        Returns entries with importance >= consolidation_threshold.
        """
        async with self._lock:
            if user_id not in self._store:
                return []
            now = time.time()
            self._evict_expired(user_id, now)
            return [
                entry
                for entry, _ in self._store[user_id]
                if entry.importance >= self._config.consolidation_threshold
            ]

    async def remove(self, user_id: str, memory_id: str) -> bool:
        """Remove a specific entry."""
        async with self._lock:
            if user_id not in self._store:
                return False
            initial_len = len(self._store[user_id])
            self._store[user_id] = [(e, t) for e, t in self._store[user_id] if e.id != memory_id]
            return len(self._store[user_id]) < initial_len

    async def remove_batch(self, user_id: str, memory_ids: set[str]) -> int:
        """Remove multiple entries by their IDs."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            initial_len = len(self._store[user_id])
            self._store[user_id] = [
                (e, t) for e, t in self._store[user_id] if e.id not in memory_ids
            ]
            return initial_len - len(self._store[user_id])

    async def count(self, user_id: str) -> int:
        """Get the number of non-expired entries for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            now = time.time()
            self._evict_expired(user_id, now)
            return len(self._store[user_id])

    async def clear(self, user_id: str) -> int:
        """Clear all short-term memory for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            count = len(self._store[user_id])
            self._store[user_id].clear()
            return count

    async def get_by_importance(
        self, user_id: str, min_importance: float = 0.0
    ) -> list[MemoryEntry]:
        """Get entries filtered by minimum importance."""
        async with self._lock:
            if user_id not in self._store:
                return []
            now = time.time()
            self._evict_expired(user_id, now)
            return [
                entry for entry, _ in self._store[user_id] if entry.importance >= min_importance
            ]

    def _evict_expired(self, user_id: str, now: float) -> None:
        """Remove all expired entries. Must hold lock."""
        if user_id not in self._store:
            return
        self._store[user_id] = [
            (e, t) for e, t in self._store[user_id] if (now - t) <= self._config.ttl_seconds
        ]

    def _evict_least_important(self, user_id: str) -> None:
        """Remove the least important entry. Must hold lock."""
        if not self._store[user_id]:
            return
        min_idx = 0
        min_importance = self._store[user_id][0][0].importance
        for i, (entry, _) in enumerate(self._store[user_id]):
            if entry.importance < min_importance:
                min_importance = entry.importance
                min_idx = i
        self._store[user_id].pop(min_idx)

    async def evict_expired(self, user_id: str) -> int:
        """Force-evict all expired entries, returning the count removed."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            now = time.time()
            before = len(self._store[user_id])
            self._store[user_id] = [
                (e, t) for e, t in self._store[user_id] if (now - t) <= self._config.ttl_seconds
            ]
            return before - len(self._store[user_id])
