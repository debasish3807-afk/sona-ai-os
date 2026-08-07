"""Unit tests for working memory manager."""

import asyncio

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.working_memory import WorkingMemoryConfig, WorkingMemoryManager


def _make_entry(id: str, content: str = "test") -> MemoryEntry:
    return MemoryEntry(id=id, memory_type=MemoryType.WORKING, content=content)


class TestWorkingMemoryStore:
    """Tests for storing entries in working memory."""

    @pytest.mark.asyncio
    async def test_store_and_get(self) -> None:
        wm = WorkingMemoryManager()
        entry = _make_entry("m1", "hello")
        await wm.store("user1", entry)
        result = await wm.get("user1", "m1")
        assert result is not None
        assert result.content == "hello"

    @pytest.mark.asyncio
    async def test_store_returns_id(self) -> None:
        wm = WorkingMemoryManager()
        entry = _make_entry("m1")
        result_id = await wm.store("user1", entry)
        assert result_id == "m1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self) -> None:
        wm = WorkingMemoryManager()
        result = await wm.get("nobody", "m1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_nonexistent_id(self) -> None:
        wm = WorkingMemoryManager()
        await wm.store("user1", _make_entry("m1"))
        result = await wm.get("user1", "m99")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        wm = WorkingMemoryManager()
        await wm.store("user1", _make_entry("m1"))
        await wm.store("user1", _make_entry("m2"))
        results = await wm.get_all("user1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_all_empty(self) -> None:
        wm = WorkingMemoryManager()
        results = await wm.get_all("user1")
        assert results == []


class TestWorkingMemoryCapacity:
    """Tests for capacity limits and eviction."""

    @pytest.mark.asyncio
    async def test_capacity_limit(self) -> None:
        config = WorkingMemoryConfig(max_capacity=5, ttl_seconds=3600)
        wm = WorkingMemoryManager(config=config)
        for i in range(10):
            await wm.store("user1", _make_entry(f"m{i}"))
        count = await wm.count("user1")
        assert count == 5

    @pytest.mark.asyncio
    async def test_evicts_oldest(self) -> None:
        config = WorkingMemoryConfig(max_capacity=3, ttl_seconds=3600)
        wm = WorkingMemoryManager(config=config)
        await wm.store("user1", _make_entry("m1"))
        await wm.store("user1", _make_entry("m2"))
        await wm.store("user1", _make_entry("m3"))
        await wm.store("user1", _make_entry("m4"))
        # m1 should have been evicted
        assert await wm.get("user1", "m1") is None
        assert await wm.get("user1", "m4") is not None

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        wm = WorkingMemoryManager()
        assert await wm.count("user1") == 0
        await wm.store("user1", _make_entry("m1"))
        assert await wm.count("user1") == 1


class TestWorkingMemoryTTL:
    """Tests for TTL-based expiration."""

    @pytest.mark.asyncio
    async def test_ttl_expiration(self) -> None:
        config = WorkingMemoryConfig(max_capacity=100, ttl_seconds=0)
        wm = WorkingMemoryManager(config=config)
        await wm.store("user1", _make_entry("m1"))
        await asyncio.sleep(0.01)
        result = await wm.get("user1", "m1")
        assert result is None

    @pytest.mark.asyncio
    async def test_non_expired_accessible(self) -> None:
        config = WorkingMemoryConfig(max_capacity=100, ttl_seconds=3600)
        wm = WorkingMemoryManager(config=config)
        await wm.store("user1", _make_entry("m1"))
        result = await wm.get("user1", "m1")
        assert result is not None


class TestWorkingMemoryOperations:
    """Tests for remove, clear, and other operations."""

    @pytest.mark.asyncio
    async def test_remove(self) -> None:
        wm = WorkingMemoryManager()
        await wm.store("user1", _make_entry("m1"))
        assert await wm.remove("user1", "m1") is True
        assert await wm.get("user1", "m1") is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self) -> None:
        wm = WorkingMemoryManager()
        assert await wm.remove("user1", "m99") is False

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        wm = WorkingMemoryManager()
        await wm.store("user1", _make_entry("m1"))
        await wm.store("user1", _make_entry("m2"))
        count = await wm.clear("user1")
        assert count == 2
        assert await wm.count("user1") == 0

    @pytest.mark.asyncio
    async def test_clear_empty(self) -> None:
        wm = WorkingMemoryManager()
        count = await wm.clear("user1")
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_recent(self) -> None:
        wm = WorkingMemoryManager()
        for i in range(5):
            await wm.store("user1", _make_entry(f"m{i}"))
        recent = await wm.get_recent("user1", limit=3)
        assert len(recent) == 3
        assert recent[0].id == "m4"

    @pytest.mark.asyncio
    async def test_get_by_session(self) -> None:
        wm = WorkingMemoryManager()
        e1 = MemoryEntry(
            id="m1",
            memory_type=MemoryType.WORKING,
            content="a",
            metadata={"session_id": "s1"},
        )
        e2 = MemoryEntry(
            id="m2",
            memory_type=MemoryType.WORKING,
            content="b",
            metadata={"session_id": "s2"},
        )
        await wm.store("user1", e1)
        await wm.store("user1", e2)
        results = await wm.get_by_session("user1", "s1")
        assert len(results) == 1
        assert results[0].id == "m1"

    @pytest.mark.asyncio
    async def test_forces_working_memory_type(self) -> None:
        wm = WorkingMemoryManager()
        entry = MemoryEntry(id="m1", memory_type=MemoryType.LONG_TERM, content="test")
        await wm.store("user1", entry)
        result = await wm.get("user1", "m1")
        assert result is not None
        assert result.memory_type == MemoryType.WORKING
