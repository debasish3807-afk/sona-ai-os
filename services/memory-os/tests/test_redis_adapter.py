"""Unit tests for the Redis adapter mock."""

import asyncio

import pytest

from sona_memory.infrastructure.redis_adapter import RedisAdapter


class TestRedisBasicOps:
    """Tests for basic SET/GET/DEL operations."""

    @pytest.mark.asyncio
    async def test_set_and_get(self) -> None:
        redis = RedisAdapter()
        await redis.set("key1", "value1")
        result = await redis.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_missing_key(self) -> None:
        redis = RedisAdapter()
        result = await redis.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing(self) -> None:
        redis = RedisAdapter()
        await redis.set("key1", "val")
        assert await redis.delete("key1") is True
        assert await redis.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        redis = RedisAdapter()
        assert await redis.delete("no_key") is False

    @pytest.mark.asyncio
    async def test_exists(self) -> None:
        redis = RedisAdapter()
        await redis.set("key1", "val")
        assert await redis.exists("key1") is True
        assert await redis.exists("no_key") is False

    @pytest.mark.asyncio
    async def test_overwrite_value(self) -> None:
        redis = RedisAdapter()
        await redis.set("key1", "first")
        await redis.set("key1", "second")
        assert await redis.get("key1") == "second"

    @pytest.mark.asyncio
    async def test_set_complex_value(self) -> None:
        redis = RedisAdapter()
        data = {"name": "test", "count": 42}
        await redis.set("obj", data)
        assert await redis.get("obj") == data


class TestRedisExpiration:
    """Tests for TTL and expiration."""

    @pytest.mark.asyncio
    async def test_set_with_expiry(self) -> None:
        redis = RedisAdapter()
        await redis.set("exp_key", "val", ex=1)
        assert await redis.get("exp_key") == "val"

    @pytest.mark.asyncio
    async def test_expired_key_returns_none(self) -> None:
        redis = RedisAdapter()
        await redis.set("exp_key", "val", ex=0)
        await asyncio.sleep(0.01)
        assert await redis.get("exp_key") is None

    @pytest.mark.asyncio
    async def test_ttl_with_expiry(self) -> None:
        redis = RedisAdapter()
        await redis.set("key1", "val", ex=100)
        ttl = await redis.ttl("key1")
        assert ttl > 0
        assert ttl <= 100

    @pytest.mark.asyncio
    async def test_ttl_without_expiry(self) -> None:
        redis = RedisAdapter()
        await redis.set("key1", "val")
        assert await redis.ttl("key1") == -1

    @pytest.mark.asyncio
    async def test_ttl_missing_key(self) -> None:
        redis = RedisAdapter()
        assert await redis.ttl("missing") == -2

    @pytest.mark.asyncio
    async def test_expire_command(self) -> None:
        redis = RedisAdapter()
        await redis.set("key1", "val")
        assert await redis.expire("key1", 60) is True
        ttl = await redis.ttl("key1")
        assert ttl > 0

    @pytest.mark.asyncio
    async def test_expire_nonexistent(self) -> None:
        redis = RedisAdapter()
        assert await redis.expire("no_key", 60) is False


class TestRedisKeys:
    """Tests for KEYS pattern matching."""

    @pytest.mark.asyncio
    async def test_keys_all(self) -> None:
        redis = RedisAdapter()
        await redis.set("a", 1)
        await redis.set("b", 2)
        keys = await redis.keys("*")
        assert set(keys) == {"a", "b"}

    @pytest.mark.asyncio
    async def test_keys_prefix(self) -> None:
        redis = RedisAdapter()
        await redis.set("user:1", "a")
        await redis.set("user:2", "b")
        await redis.set("other:1", "c")
        keys = await redis.keys("user:*")
        assert set(keys) == {"user:1", "user:2"}

    @pytest.mark.asyncio
    async def test_keys_empty(self) -> None:
        redis = RedisAdapter()
        keys = await redis.keys("*")
        assert keys == []


class TestRedisList:
    """Tests for list operations."""

    @pytest.mark.asyncio
    async def test_lpush_and_lrange(self) -> None:
        redis = RedisAdapter()
        await redis.lpush("list1", "a", "b")
        result = await redis.lrange("list1", 0, -1)
        assert result == ["b", "a"]

    @pytest.mark.asyncio
    async def test_rpush_and_lrange(self) -> None:
        redis = RedisAdapter()
        await redis.rpush("list1", "a", "b")
        result = await redis.lrange("list1", 0, -1)
        assert result == ["a", "b"]

    @pytest.mark.asyncio
    async def test_llen(self) -> None:
        redis = RedisAdapter()
        await redis.rpush("list1", "a", "b", "c")
        assert await redis.llen("list1") == 3

    @pytest.mark.asyncio
    async def test_llen_empty(self) -> None:
        redis = RedisAdapter()
        assert await redis.llen("no_list") == 0

    @pytest.mark.asyncio
    async def test_ltrim(self) -> None:
        redis = RedisAdapter()
        await redis.rpush("list1", "a", "b", "c", "d")
        await redis.ltrim("list1", 1, 2)
        result = await redis.lrange("list1", 0, -1)
        assert result == ["b", "c"]

    @pytest.mark.asyncio
    async def test_lrange_partial(self) -> None:
        redis = RedisAdapter()
        await redis.rpush("list1", "a", "b", "c", "d")
        result = await redis.lrange("list1", 0, 1)
        assert result == ["a", "b"]


class TestRedisHash:
    """Tests for hash operations."""

    @pytest.mark.asyncio
    async def test_hset_and_hget(self) -> None:
        redis = RedisAdapter()
        await redis.hset("hash1", "field1", "value1")
        result = await redis.hget("hash1", "field1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_hget_missing(self) -> None:
        redis = RedisAdapter()
        assert await redis.hget("hash1", "field") is None

    @pytest.mark.asyncio
    async def test_hgetall(self) -> None:
        redis = RedisAdapter()
        await redis.hset("hash1", "a", 1)
        await redis.hset("hash1", "b", 2)
        result = await redis.hgetall("hash1")
        assert result == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_hdel(self) -> None:
        redis = RedisAdapter()
        await redis.hset("hash1", "field1", "val")
        assert await redis.hdel("hash1", "field1") == 1
        assert await redis.hget("hash1", "field1") is None

    @pytest.mark.asyncio
    async def test_hdel_missing(self) -> None:
        redis = RedisAdapter()
        assert await redis.hdel("hash1", "no_field") == 0

    @pytest.mark.asyncio
    async def test_flushall(self) -> None:
        redis = RedisAdapter()
        await redis.set("k1", "v1")
        await redis.set("k2", "v2")
        await redis.flushall()
        assert await redis.get("k1") is None
        assert await redis.get("k2") is None
