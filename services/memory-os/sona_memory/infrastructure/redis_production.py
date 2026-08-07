"""Production Redis adapter using redis-py async client.

Uses redis.asyncio for actual Redis connectivity when available.
Falls back gracefully to the in-memory mock adapter if Redis is unavailable.
"""

import asyncio
import json
from typing import Any

import structlog

from sona_memory.infrastructure.redis_adapter import RedisAdapter

logger = structlog.get_logger()


class RedisProductionAdapter:
    """Production Redis adapter with connection pooling and retry.

    Wraps the mock RedisAdapter as a fallback, attempting to connect to
    a real Redis instance. When the real Redis is unavailable, all
    operations transparently fall back to the in-memory mock.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        max_connections: int = 50,
        socket_timeout: float = 5.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self._url = url
        self._max_connections = max_connections
        self._socket_timeout = socket_timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._connected = False
        self._use_real: bool = False
        # Fallback to in-memory mock
        self._backend = RedisAdapter()

    async def connect(self) -> bool:
        """Attempt to connect to Redis with exponential backoff retry.

        Returns True if connection was established, False if falling back
        to mock adapter.
        """
        for attempt in range(self._max_retries):
            try:
                # Try importing redis.asyncio for real connection
                import redis.asyncio as aioredis

                pool = aioredis.ConnectionPool.from_url(
                    self._url,
                    max_connections=self._max_connections,
                    socket_timeout=self._socket_timeout,
                )
                client = aioredis.Redis(connection_pool=pool)
                await client.ping()
                self._real_client = client
                self._use_real = True
                self._connected = True
                await logger.ainfo(
                    "redis.connected",
                    url=self._url,
                    attempt=attempt + 1,
                )
                return True
            except ImportError:
                await logger.awarning(
                    "redis.library_not_installed",
                    message="redis-py not installed, using mock backend",
                )
                self._connected = True
                return False
            except Exception as exc:  # noqa: BLE001
                delay = self._retry_delay * (2**attempt)
                await logger.awarning(
                    "redis.connect_retry",
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    delay=delay,
                    error=str(exc),
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(delay)

        await logger.awarning(
            "redis.fallback_to_mock",
            url=self._url,
            message="All connection attempts failed, using mock backend",
        )
        self._connected = True
        return False

    async def disconnect(self) -> None:
        """Close Redis connection and release pool."""
        if self._use_real and hasattr(self, "_real_client"):
            try:
                await self._real_client.close()
            except Exception as exc:  # noqa: BLE001
                await logger.awarning("redis.disconnect_error", error=str(exc))
        self._connected = False
        self._use_real = False
        await logger.ainfo("redis.disconnected")

    async def ping(self) -> bool:
        """Check if Redis is responding."""
        if self._use_real and hasattr(self, "_real_client"):
            try:
                result: bool = await self._real_client.ping()
                return result
            except Exception:  # noqa: BLE001
                return False
        # Mock is always "available"
        return self._connected

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a key-value pair with optional TTL."""
        if self._use_real and hasattr(self, "_real_client"):
            serialized = json.dumps(value) if not isinstance(value, str) else value
            await self._real_client.set(key, serialized, ex=ttl)
        else:
            await self._backend.set(key, value, ex=ttl)

    async def get(self, key: str) -> Any | None:
        """Get value by key."""
        if self._use_real and hasattr(self, "_real_client"):
            raw = await self._real_client.get(key)
            if raw is None:
                return None
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return raw.decode() if isinstance(raw, bytes) else raw
        return await self._backend.get(key)

    async def delete(self, key: str) -> bool:
        """Delete a key."""
        if self._use_real and hasattr(self, "_real_client"):
            result = await self._real_client.delete(key)
            return bool(result)
        return await self._backend.delete(key)

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern."""
        if self._use_real and hasattr(self, "_real_client"):
            raw_keys = await self._real_client.keys(pattern)
            return [k.decode() if isinstance(k, bytes) else k for k in raw_keys]
        return await self._backend.keys(pattern)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set TTL on existing key."""
        if self._use_real and hasattr(self, "_real_client"):
            result = await self._real_client.expire(key, seconds)
            return bool(result)
        return await self._backend.expire(key, seconds)

    async def rpush(self, key: str, value: Any) -> int:
        """Push value to right of list."""
        if self._use_real and hasattr(self, "_real_client"):
            serialized = json.dumps(value) if not isinstance(value, str) else value
            result: int = await self._real_client.rpush(key, serialized)
            return result
        return await self._backend.rpush(key, value)

    async def lrange(self, key: str, start: int, stop: int) -> list[Any]:
        """Get range of elements from list."""
        if self._use_real and hasattr(self, "_real_client"):
            raw_list = await self._real_client.lrange(key, start, stop)
            results: list[Any] = []
            for item in raw_list:
                try:
                    decoded = item.decode() if isinstance(item, bytes) else item
                    results.append(json.loads(decoded))
                except (json.JSONDecodeError, TypeError):
                    results.append(item.decode() if isinstance(item, bytes) else item)
            return results
        return await self._backend.lrange(key, start, stop)

    async def ltrim(self, key: str, start: int, stop: int) -> None:
        """Trim list to specified range."""
        if self._use_real and hasattr(self, "_real_client"):
            await self._real_client.ltrim(key, start, stop)
        else:
            await self._backend.ltrim(key, start, stop)

    @property
    def is_connected(self) -> bool:
        """Whether the adapter has an active connection (real or mock)."""
        return self._connected

    @property
    def is_using_real_redis(self) -> bool:
        """Whether the adapter is using a real Redis connection."""
        return self._use_real
