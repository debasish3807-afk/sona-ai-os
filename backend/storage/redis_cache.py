"""Redis caching layer for Sona AI OS.

Provides async caching with TTL, key prefixing, and JSON serialization.
Falls back to an in-memory LRU cache when Redis is unavailable.

Requires: redis[hiredis] (pip install redis[hiredis])
Configure via REDIS_URL env var: redis://localhost:6379/0
"""

from __future__ import annotations

import json
import os
import time
from collections import OrderedDict
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)

DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_TTL = 300  # 5 minutes
DEFAULT_PREFIX = "sona:"
MAX_MEMORY_CACHE_SIZE = 1000


class RedisCache:
    """Async Redis cache with in-memory fallback.

    When Redis is available, uses it for distributed caching.
    When unavailable, operates with a local LRU cache (single-node).
    """

    def __init__(
        self,
        redis_url: str | None = None,
        default_ttl: int = DEFAULT_TTL,
        prefix: str = DEFAULT_PREFIX,
    ) -> None:
        self._redis_url = redis_url or os.environ.get("REDIS_URL", DEFAULT_REDIS_URL)
        self._default_ttl = default_ttl
        self._prefix = prefix
        self._redis: Any = None
        self._available = False
        # In-memory fallback (LRU with TTL)
        self._local_cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

    async def initialize(self) -> None:
        """Connect to Redis. Falls back to local cache if unavailable."""
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=5,
            )
            # Test connection
            await self._redis.ping()
            self._available = True
            logger.info("redis_connected", url=self._redis_url.split("@")[-1])
        except ImportError:
            logger.warning("redis_not_installed", hint="pip install redis[hiredis]")
            self._available = False
        except Exception as exc:
            logger.warning("redis_unavailable", error=str(exc))
            self._available = False

    async def shutdown(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None
        self._available = False
        logger.info("redis_shutdown")

    @property
    def is_available(self) -> bool:
        """Whether Redis is connected."""
        return self._available

    # --- Core Operations ---

    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if not found or expired."""
        full_key = self._prefix + key

        if self._available:
            try:
                raw = await self._redis.get(full_key)
                if raw is not None:
                    self._stats["hits"] += 1
                    return json.loads(raw)
                self._stats["misses"] += 1
                return None
            except Exception:
                pass

        # Fallback to local cache
        entry = self._local_cache.get(full_key)
        if entry is not None:
            value, expires_at = entry
            if expires_at > time.time():
                self._stats["hits"] += 1
                self._local_cache.move_to_end(full_key)
                return value
            # Expired
            del self._local_cache[full_key]
        self._stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value with optional TTL (seconds)."""
        full_key = self._prefix + key
        ttl = ttl if ttl is not None else self._default_ttl
        serialized = json.dumps(value)
        self._stats["sets"] += 1

        if self._available:
            try:
                await self._redis.setex(full_key, ttl, serialized)
                return
            except Exception:
                pass

        # Fallback to local cache
        self._local_cache[full_key] = (value, time.time() + ttl)
        self._local_cache.move_to_end(full_key)
        # Evict oldest if over limit
        while len(self._local_cache) > MAX_MEMORY_CACHE_SIZE:
            self._local_cache.popitem(last=False)

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if existed."""
        full_key = self._prefix + key
        self._stats["deletes"] += 1

        if self._available:
            try:
                result = await self._redis.delete(full_key)
                return bool(result)
            except Exception:
                pass

        # Fallback
        if full_key in self._local_cache:
            del self._local_cache[full_key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        return (await self.get(key)) is not None

    async def clear_prefix(self, prefix: str) -> int:
        """Delete all keys matching a prefix. Returns count deleted."""
        full_prefix = self._prefix + prefix
        count = 0

        if self._available:
            try:
                cursor = "0"
                while cursor != 0:
                    cursor, keys = await self._redis.scan(
                        cursor=cursor, match=f"{full_prefix}*", count=100
                    )
                    if keys:
                        count += await self._redis.delete(*keys)
                return count
            except Exception:
                pass

        # Fallback: scan local cache
        to_delete = [k for k in self._local_cache if k.startswith(full_prefix)]
        for k in to_delete:
            del self._local_cache[k]
        return len(to_delete)

    async def get_or_set(self, key: str, factory: Any, ttl: int | None = None) -> Any:
        """Get cached value or compute and store it.

        Args:
            key: Cache key
            factory: Async callable that produces the value if not cached
            ttl: Optional TTL override
        """
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl=ttl)
        return value

    # --- Stats ---

    def get_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0
        return {
            "available": self._available,
            "backend": "redis" if self._available else "memory",
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 4),
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "local_cache_size": len(self._local_cache),
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}
