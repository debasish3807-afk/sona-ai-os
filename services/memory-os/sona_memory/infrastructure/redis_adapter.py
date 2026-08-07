"""Mock Redis adapter for in-memory simulation.

Provides an async interface matching real Redis usage patterns,
backed by an in-memory dictionary for working and short-term memory.
"""

import asyncio
import time
from typing import Any


class RedisAdapter:
    """In-memory mock of Redis operations.

    Simulates SET/GET/DEL/EXPIRE/KEYS/TTL operations with proper
    TTL-based expiration semantics.
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key in self._expiry:
            return time.time() > self._expiry[key]
        return False

    def _cleanup_key(self, key: str) -> None:
        """Remove an expired key."""
        self._store.pop(key, None)
        self._expiry.pop(key, None)

    async def set(self, key: str, value: Any, ex: int | None = None) -> None:
        """Set a key-value pair with optional expiration in seconds."""
        async with self._lock:
            self._store[key] = value
            if ex is not None:
                self._expiry[key] = time.time() + ex
            elif key in self._expiry:
                del self._expiry[key]

    async def get(self, key: str) -> Any | None:
        """Get a value by key, returning None if expired or missing."""
        async with self._lock:
            if self._is_expired(key):
                self._cleanup_key(key)
                return None
            return self._store.get(key)

    async def delete(self, key: str) -> bool:
        """Delete a key, returning True if it existed."""
        async with self._lock:
            if key in self._store:
                del self._store[key]
                self._expiry.pop(key, None)
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        async with self._lock:
            if self._is_expired(key):
                self._cleanup_key(key)
                return False
            return key in self._store

    async def expire(self, key: str, seconds: int) -> bool:
        """Set TTL on an existing key."""
        async with self._lock:
            if key not in self._store:
                return False
            if self._is_expired(key):
                self._cleanup_key(key)
                return False
            self._expiry[key] = time.time() + seconds
            return True

    async def ttl(self, key: str) -> int:
        """Get remaining TTL in seconds. Returns -1 if no TTL, -2 if missing."""
        async with self._lock:
            if key not in self._store or self._is_expired(key):
                if self._is_expired(key):
                    self._cleanup_key(key)
                return -2
            if key not in self._expiry:
                return -1
            remaining = self._expiry[key] - time.time()
            return max(0, int(remaining))

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching a pattern. Supports simple prefix* patterns."""
        async with self._lock:
            # Clean expired keys first
            expired = [k for k in self._store if self._is_expired(k)]
            for k in expired:
                self._cleanup_key(k)

            if pattern == "*":
                return list(self._store.keys())

            if pattern.endswith("*"):
                prefix = pattern[:-1]
                return [k for k in self._store if k.startswith(prefix)]

            return [k for k in self._store if k == pattern]

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of a list."""
        async with self._lock:
            if key not in self._store:
                self._store[key] = []
            lst = self._store[key]
            for v in values:
                lst.insert(0, v)
            return len(lst)

    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to the right of a list."""
        async with self._lock:
            if key not in self._store:
                self._store[key] = []
            lst = self._store[key]
            lst.extend(values)
            return len(lst)

    async def lrange(self, key: str, start: int, stop: int) -> list[Any]:
        """Get a range of elements from a list."""
        async with self._lock:
            if key not in self._store:
                return []
            lst = self._store[key]
            if stop == -1:
                return lst[start:]
            return lst[start : stop + 1]

    async def ltrim(self, key: str, start: int, stop: int) -> None:
        """Trim a list to the specified range."""
        async with self._lock:
            if key not in self._store:
                return
            lst = self._store[key]
            if stop == -1:
                self._store[key] = lst[start:]
            else:
                self._store[key] = lst[start : stop + 1]

    async def llen(self, key: str) -> int:
        """Get the length of a list."""
        async with self._lock:
            if key not in self._store:
                return 0
            return len(self._store[key])

    async def hset(self, key: str, field: str, value: Any) -> int:
        """Set a hash field."""
        async with self._lock:
            if key not in self._store:
                self._store[key] = {}
            is_new = field not in self._store[key]
            self._store[key][field] = value
            return 1 if is_new else 0

    async def hget(self, key: str, field: str) -> Any | None:
        """Get a hash field value."""
        async with self._lock:
            if key not in self._store:
                return None
            return self._store[key].get(field)

    async def hgetall(self, key: str) -> dict[str, Any]:
        """Get all fields and values in a hash."""
        async with self._lock:
            if key not in self._store:
                return {}
            return dict(self._store[key])

    async def hdel(self, key: str, field: str) -> int:
        """Delete a hash field."""
        async with self._lock:
            if key not in self._store:
                return 0
            if field in self._store[key]:
                del self._store[key][field]
                return 1
            return 0

    async def flushall(self) -> None:
        """Clear all data."""
        async with self._lock:
            self._store.clear()
            self._expiry.clear()
