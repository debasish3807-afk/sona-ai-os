"""Working memory manager.

Provides fast, bounded-capacity memory for active conversation context.
Features auto-eviction of oldest entries when capacity is exceeded
and TTL-based expiration.
"""

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from sona_memory.domain.models import MemoryEntry, MemoryType


@dataclass
class WorkingMemoryConfig:
    """Configuration for working memory."""

    max_capacity: int = 100
    ttl_seconds: int = 1800  # 30 minutes


class WorkingMemoryManager:
    """Bounded working memory with fast access and auto-eviction.

    Uses an OrderedDict for O(1) access with LRU-like eviction.
    Entries expire after the configured TTL.
    """

    def __init__(self, config: WorkingMemoryConfig | None = None) -> None:
        self._config = config or WorkingMemoryConfig()
        # user_id -> OrderedDict[memory_id -> (entry, insert_time)]
        self._store: dict[str, OrderedDict[str, tuple[MemoryEntry, float]]] = {}
        self._lock = asyncio.Lock()

    @property
    def config(self) -> WorkingMemoryConfig:
        """Current configuration."""
        return self._config

    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store an entry in working memory.

        Evicts oldest entries if capacity is exceeded.
        """
        async with self._lock:
            if user_id not in self._store:
                self._store[user_id] = OrderedDict()

            user_mem = self._store[user_id]
            now = time.time()

            # Remove expired entries first
            self._evict_expired(user_id, now)

            # Evict oldest if at capacity
            while len(user_mem) >= self._config.max_capacity:
                user_mem.popitem(last=False)

            # Ensure memory type is WORKING
            if entry.memory_type != MemoryType.WORKING:
                entry = replace(entry, memory_type=MemoryType.WORKING)

            user_mem[entry.id] = (entry, now)
            return entry.id

    async def get(self, user_id: str, memory_id: str) -> MemoryEntry | None:
        """Get a specific entry by ID."""
        async with self._lock:
            if user_id not in self._store:
                return None
            item = self._store[user_id].get(memory_id)
            if item is None:
                return None
            entry, insert_time = item
            if self._is_expired(insert_time):
                del self._store[user_id][memory_id]
                return None
            return entry

    async def get_all(self, user_id: str) -> list[MemoryEntry]:
        """Get all non-expired entries for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            now = time.time()
            self._evict_expired(user_id, now)
            return [entry for entry, _ in self._store[user_id].values()]

    async def get_recent(self, user_id: str, limit: int = 10) -> list[MemoryEntry]:
        """Get the most recent entries for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            now = time.time()
            self._evict_expired(user_id, now)
            items = list(self._store[user_id].values())
            recent = items[-limit:]
            recent.reverse()
            return [entry for entry, _ in recent]

    async def remove(self, user_id: str, memory_id: str) -> bool:
        """Remove a specific entry."""
        async with self._lock:
            if user_id not in self._store:
                return False
            if memory_id in self._store[user_id]:
                del self._store[user_id][memory_id]
                return True
            return False

    async def count(self, user_id: str) -> int:
        """Get the number of non-expired entries for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            now = time.time()
            self._evict_expired(user_id, now)
            return len(self._store[user_id])

    async def clear(self, user_id: str) -> int:
        """Clear all working memory for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            count = len(self._store[user_id])
            self._store[user_id].clear()
            return count

    async def get_by_session(self, user_id: str, session_id: str) -> list[MemoryEntry]:
        """Get entries filtered by session metadata."""
        async with self._lock:
            if user_id not in self._store:
                return []
            now = time.time()
            self._evict_expired(user_id, now)
            results: list[MemoryEntry] = []
            for entry, _ in self._store[user_id].values():
                if entry.metadata and entry.metadata.get("session_id") == session_id:
                    results.append(entry)
            return results

    async def get_expires_at(self, user_id: str, memory_id: str) -> datetime | None:
        """Get the expiration time for a memory entry."""
        async with self._lock:
            if user_id not in self._store:
                return None
            item = self._store[user_id].get(memory_id)
            if item is None:
                return None
            _, insert_time = item
            expire_time = insert_time + self._config.ttl_seconds
            return datetime.fromtimestamp(expire_time, tz=UTC)

    def _is_expired(self, insert_time: float) -> bool:
        """Check if an entry has expired based on insert time."""
        return (time.time() - insert_time) > self._config.ttl_seconds

    def _evict_expired(self, user_id: str, now: float) -> None:
        """Remove all expired entries for a user. Must hold lock."""
        if user_id not in self._store:
            return
        user_mem = self._store[user_id]
        expired_keys = [
            k
            for k, (_, insert_time) in user_mem.items()
            if (now - insert_time) > self._config.ttl_seconds
        ]
        for k in expired_keys:
            del user_mem[k]

    async def expire_entries(self, user_id: str, before: datetime) -> int:
        """Manually expire entries created before a given time."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            cutoff = before.timestamp()
            expired_keys = [
                k for k, (_, insert_time) in self._store[user_id].items() if insert_time < cutoff
            ]
            for k in expired_keys:
                del self._store[user_id][k]
            return len(expired_keys)

    async def evict_expired(self, user_id: str) -> int:
        """Force-evict all expired entries, returning the count removed."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            now = time.time()
            user_mem = self._store[user_id]
            expired_keys = [
                k
                for k, (_, insert_time) in user_mem.items()
                if (now - insert_time) > self._config.ttl_seconds
            ]
            for k in expired_keys:
                del user_mem[k]
            return len(expired_keys)
