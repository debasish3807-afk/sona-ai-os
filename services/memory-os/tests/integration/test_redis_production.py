"""Integration tests for production Redis adapter.

These tests require a running Redis instance.
They are automatically skipped if Redis is not available.
"""

import asyncio

import pytest

from sona_memory.infrastructure.redis_production import RedisProductionAdapter


def _redis_available() -> bool:
    """Check if Redis is available for testing."""
    try:
        import redis  # type: ignore[import-untyped]

        client = redis.Redis.from_url("redis://localhost:6379/0")
        client.ping()
        client.close()
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(not _redis_available(), reason="Redis not running")


class TestRedisProductionAdapter:
    """Integration tests for RedisProductionAdapter with real Redis."""

    @pytest.fixture
    async def adapter(self) -> RedisProductionAdapter:
        """Create and connect a production adapter."""
        adapter = RedisProductionAdapter(
            url="redis://localhost:6379/0",
            max_retries=1,
            retry_delay=0.1,
        )
        await adapter.connect()
        yield adapter  # type: ignore[misc]
        await adapter.disconnect()

    async def test_connect(self, adapter: RedisProductionAdapter) -> None:
        """Test that connection is established."""
        assert adapter.is_connected

    async def test_set_get(self, adapter: RedisProductionAdapter) -> None:
        """Test basic set and get operations."""
        await adapter.set("test:key", {"hello": "world"})
        result = await adapter.get("test:key")
        assert result == {"hello": "world"}
        await adapter.delete("test:key")

    async def test_ttl_expiration(self, adapter: RedisProductionAdapter) -> None:
        """Test that keys expire after TTL."""
        await adapter.set("test:ttl", "expires", ttl=1)
        result = await adapter.get("test:ttl")
        assert result is not None
        await asyncio.sleep(1.1)
        result = await adapter.get("test:ttl")
        assert result is None

    async def test_list_operations(self, adapter: RedisProductionAdapter) -> None:
        """Test list push, range, and trim."""
        key = "test:list"
        await adapter.delete(key)
        await adapter.rpush(key, "item1")
        await adapter.rpush(key, "item2")
        await adapter.rpush(key, "item3")
        items = await adapter.lrange(key, 0, -1)
        assert len(items) == 3
        await adapter.ltrim(key, 0, 1)
        items = await adapter.lrange(key, 0, -1)
        assert len(items) == 2
        await adapter.delete(key)

    async def test_reconnection(self, adapter: RedisProductionAdapter) -> None:
        """Test that ping works after connection."""
        result = await adapter.ping()
        assert result is True


class TestRedisProductionAdapterFallback:
    """Tests for fallback behavior when Redis is unavailable."""

    async def test_fallback_to_mock(self) -> None:
        """Adapter falls back to mock when Redis is unreachable."""
        adapter = RedisProductionAdapter(
            url="redis://nonexistent-host:9999/0",
            max_retries=1,
            retry_delay=0.01,
        )
        await adapter.connect()
        # Should still be "connected" (using mock fallback)
        assert adapter.is_connected
        # Basic operations should work via mock
        await adapter.set("fallback:key", "value")
        result = await adapter.get("fallback:key")
        assert result == "value"
        await adapter.disconnect()
