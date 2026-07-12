"""Capability Cache — in-memory caching for capability results."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class CapabilityCache:
    """In-memory cache with TTL support for capability results.

    Provides key-value storage with automatic expiration,
    prefix-based invalidation, and hit/miss statistics.
    """

    def __init__(self, max_entries: int = 1000, ttl_seconds: int = 300) -> None:
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[Any, float]] = {}
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str) -> Any | None:
        """Get a cached value by key.

        Returns:
            The cached value, or None if not found or expired.
        """
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None

        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            self._misses += 1
            return None

        self._hits += 1
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        if len(self._store) >= self._max_entries:
            self._evict_expired()
            if len(self._store) >= self._max_entries:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]

        expires_at = time.time() + self._ttl_seconds
        self._store[key] = (value, expires_at)

    def invalidate(self, key: str) -> None:
        """Remove a specific key from the cache."""
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove all keys matching a prefix.

        Args:
            prefix: The key prefix to match.
        """
        keys_to_remove = [k for k in self._store if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._store[key]

    def clear(self) -> None:
        """Clear the entire cache."""
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with hits, misses, and current size.
        """
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._store),
        }

    def _evict_expired(self) -> None:
        """Remove all expired entries from the cache."""
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for key in expired:
            del self._store[key]
