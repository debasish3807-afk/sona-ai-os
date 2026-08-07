"""Unit tests for short-term memory manager."""

import asyncio

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.short_term_memory import ShortTermConfig, ShortTermMemory


def _make_entry(id: str, importance: float = 0.5, content: str = "test") -> MemoryEntry:
    return MemoryEntry(
        id=id, memory_type=MemoryType.SHORT_TERM, content=content, importance=importance
    )


class TestShortTermStore:
    """Tests for basic store and retrieve."""

    @pytest.mark.asyncio
    async def test_store_and_get(self) -> None:
        stm = ShortTermMemory()
        entry = _make_entry("m1", content="hello")
        await stm.store("user1", entry)
        result = await stm.get("user1", "m1")
        assert result is not None
        assert result.content == "hello"

    @pytest.mark.asyncio
    async def test_store_returns_id(self) -> None:
        stm = ShortTermMemory()
        result_id = await stm.store("user1", _make_entry("m1"))
        assert result_id == "m1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self) -> None:
        stm = ShortTermMemory()
        assert await stm.get("user1", "m99") is None

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        stm = ShortTermMemory()
        await stm.store("user1", _make_entry("m1"))
        await stm.store("user1", _make_entry("m2"))
        results = await stm.get_all("user1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_all_empty(self) -> None:
        stm = ShortTermMemory()
        assert await stm.get_all("user1") == []

    @pytest.mark.asyncio
    async def test_forces_short_term_type(self) -> None:
        stm = ShortTermMemory()
        entry = MemoryEntry(id="m1", memory_type=MemoryType.WORKING, content="test")
        await stm.store("user1", entry)
        result = await stm.get("user1", "m1")
        assert result is not None
        assert result.memory_type == MemoryType.SHORT_TERM


class TestShortTermCapacity:
    """Tests for capacity and importance-based eviction."""

    @pytest.mark.asyncio
    async def test_capacity_limit(self) -> None:
        config = ShortTermConfig(max_capacity=5, ttl_seconds=3600)
        stm = ShortTermMemory(config=config)
        for i in range(10):
            await stm.store("user1", _make_entry(f"m{i}", importance=i * 0.1))
        count = await stm.count("user1")
        assert count == 5

    @pytest.mark.asyncio
    async def test_evicts_least_important(self) -> None:
        config = ShortTermConfig(max_capacity=3, ttl_seconds=3600)
        stm = ShortTermMemory(config=config)
        await stm.store("user1", _make_entry("low", importance=0.1))
        await stm.store("user1", _make_entry("mid", importance=0.5))
        await stm.store("user1", _make_entry("high", importance=0.9))
        # This should evict "low"
        await stm.store("user1", _make_entry("new", importance=0.6))
        assert await stm.get("user1", "low") is None
        assert await stm.get("user1", "high") is not None
        assert await stm.get("user1", "new") is not None

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        stm = ShortTermMemory()
        assert await stm.count("user1") == 0
        await stm.store("user1", _make_entry("m1"))
        assert await stm.count("user1") == 1


class TestShortTermTTL:
    """Tests for TTL-based expiration."""

    @pytest.mark.asyncio
    async def test_expired_entry_not_returned(self) -> None:
        config = ShortTermConfig(max_capacity=100, ttl_seconds=0)
        stm = ShortTermMemory(config=config)
        await stm.store("user1", _make_entry("m1"))
        await asyncio.sleep(0.01)
        result = await stm.get("user1", "m1")
        assert result is None

    @pytest.mark.asyncio
    async def test_non_expired_accessible(self) -> None:
        config = ShortTermConfig(max_capacity=100, ttl_seconds=3600)
        stm = ShortTermMemory(config=config)
        await stm.store("user1", _make_entry("m1"))
        result = await stm.get("user1", "m1")
        assert result is not None


class TestShortTermOperations:
    """Tests for remove, clear, consolidation candidates."""

    @pytest.mark.asyncio
    async def test_remove(self) -> None:
        stm = ShortTermMemory()
        await stm.store("user1", _make_entry("m1"))
        assert await stm.remove("user1", "m1") is True
        assert await stm.get("user1", "m1") is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self) -> None:
        stm = ShortTermMemory()
        assert await stm.remove("user1", "m99") is False

    @pytest.mark.asyncio
    async def test_remove_batch(self) -> None:
        stm = ShortTermMemory()
        await stm.store("user1", _make_entry("m1"))
        await stm.store("user1", _make_entry("m2"))
        await stm.store("user1", _make_entry("m3"))
        removed = await stm.remove_batch("user1", {"m1", "m3"})
        assert removed == 2
        assert await stm.count("user1") == 1

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        stm = ShortTermMemory()
        await stm.store("user1", _make_entry("m1"))
        await stm.store("user1", _make_entry("m2"))
        count = await stm.clear("user1")
        assert count == 2
        assert await stm.count("user1") == 0

    @pytest.mark.asyncio
    async def test_get_consolidation_candidates(self) -> None:
        config = ShortTermConfig(consolidation_threshold=0.7)
        stm = ShortTermMemory(config=config)
        await stm.store("user1", _make_entry("low", importance=0.3))
        await stm.store("user1", _make_entry("high", importance=0.8))
        await stm.store("user1", _make_entry("very_high", importance=0.95))
        candidates = await stm.get_consolidation_candidates("user1")
        assert len(candidates) == 2
        ids = {c.id for c in candidates}
        assert "high" in ids
        assert "very_high" in ids

    @pytest.mark.asyncio
    async def test_get_by_importance(self) -> None:
        stm = ShortTermMemory()
        await stm.store("user1", _make_entry("low", importance=0.2))
        await stm.store("user1", _make_entry("high", importance=0.8))
        results = await stm.get_by_importance("user1", min_importance=0.5)
        assert len(results) == 1
        assert results[0].id == "high"
