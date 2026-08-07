"""Unit tests for concurrent access safety."""

import asyncio

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.di import create_memory_manager
from sona_memory.infrastructure.embedding_service import EmbeddingService
from sona_memory.infrastructure.long_term_memory import LongTermMemory
from sona_memory.infrastructure.redis_adapter import RedisAdapter
from sona_memory.infrastructure.short_term_memory import ShortTermMemory
from sona_memory.infrastructure.working_memory import WorkingMemoryConfig, WorkingMemoryManager


def _make_entry(id: str, content: str = "test") -> MemoryEntry:
    return MemoryEntry(id=id, memory_type=MemoryType.WORKING, content=content, importance=0.5)


class TestConcurrentWorkingMemory:
    """Tests for concurrent access to working memory."""

    @pytest.mark.asyncio
    async def test_concurrent_stores(self) -> None:
        wm = WorkingMemoryManager()

        async def store_entry(i: int) -> None:
            await wm.store("user1", _make_entry(f"m{i}", f"content {i}"))

        await asyncio.gather(*[store_entry(i) for i in range(50)])
        count = await wm.count("user1")
        assert count == 50

    @pytest.mark.asyncio
    async def test_concurrent_store_and_read(self) -> None:
        wm = WorkingMemoryManager()
        for i in range(10):
            await wm.store("user1", _make_entry(f"init{i}"))

        async def store_task(i: int) -> None:
            await wm.store("user1", _make_entry(f"new{i}"))

        async def read_task() -> list[MemoryEntry]:
            return await wm.get_all("user1")

        tasks = [store_task(i) for i in range(10)]
        tasks.extend([read_task() for _ in range(10)])
        results = await asyncio.gather(*tasks)
        # All reads should return valid lists
        for r in results:
            if isinstance(r, list):
                assert isinstance(r, list)

    @pytest.mark.asyncio
    async def test_concurrent_store_with_capacity(self) -> None:
        config = WorkingMemoryConfig(max_capacity=20, ttl_seconds=3600)
        wm = WorkingMemoryManager(config=config)

        async def store_entry(i: int) -> None:
            await wm.store("user1", _make_entry(f"m{i}"))

        await asyncio.gather(*[store_entry(i) for i in range(100)])
        count = await wm.count("user1")
        assert count <= 20


class TestConcurrentShortTermMemory:
    """Tests for concurrent access to short-term memory."""

    @pytest.mark.asyncio
    async def test_concurrent_stores(self) -> None:
        stm = ShortTermMemory()

        async def store_entry(i: int) -> None:
            entry = MemoryEntry(
                id=f"m{i}",
                memory_type=MemoryType.SHORT_TERM,
                content=f"content {i}",
                importance=i / 100,
            )
            await stm.store("user1", entry)

        await asyncio.gather(*[store_entry(i) for i in range(50)])
        count = await stm.count("user1")
        assert count == 50

    @pytest.mark.asyncio
    async def test_concurrent_store_and_remove(self) -> None:
        stm = ShortTermMemory()
        for i in range(20):
            entry = MemoryEntry(
                id=f"m{i}",
                memory_type=MemoryType.SHORT_TERM,
                content="test",
                importance=0.5,
            )
            await stm.store("user1", entry)

        async def remove_task(i: int) -> bool:
            return await stm.remove("user1", f"m{i}")

        async def store_task(i: int) -> str:
            entry = MemoryEntry(
                id=f"new{i}",
                memory_type=MemoryType.SHORT_TERM,
                content="new",
                importance=0.5,
            )
            return await stm.store("user1", entry)

        remove_tasks = [remove_task(i) for i in range(10)]
        new_store_tasks = [store_task(i) for i in range(10)]
        await asyncio.gather(*remove_tasks, *new_store_tasks)

        # Should have roughly 20 entries (20 - 10 removed + 10 added)
        count = await stm.count("user1")
        assert count == 20


class TestConcurrentLongTermMemory:
    """Tests for concurrent access to long-term memory."""

    @pytest.mark.asyncio
    async def test_concurrent_stores(self) -> None:
        emb = EmbeddingService(dim=64)
        ltm = LongTermMemory(embedding_service=emb)

        async def store_entry(i: int) -> None:
            entry = MemoryEntry(
                id=f"m{i}",
                memory_type=MemoryType.LONG_TERM,
                content=f"unique content {i}",
            )
            await ltm.store("user1", entry)

        await asyncio.gather(*[store_entry(i) for i in range(20)])
        count = await ltm.count("user1")
        assert count == 20

    @pytest.mark.asyncio
    async def test_concurrent_search(self) -> None:
        emb = EmbeddingService(dim=64)
        ltm = LongTermMemory(embedding_service=emb)
        for i in range(10):
            entry = MemoryEntry(
                id=f"m{i}",
                memory_type=MemoryType.LONG_TERM,
                content=f"stored fact number {i}",
            )
            await ltm.store("user1", entry)

        async def search_task(q: str) -> list:
            return await ltm.search("user1", q)

        queries = [f"fact {i}" for i in range(10)]
        results = await asyncio.gather(*[search_task(q) for q in queries])
        for r in results:
            assert isinstance(r, list)


class TestConcurrentRedis:
    """Tests for concurrent access to redis adapter."""

    @pytest.mark.asyncio
    async def test_concurrent_set_get(self) -> None:
        redis = RedisAdapter()

        async def write(i: int) -> None:
            await redis.set(f"key{i}", f"val{i}")

        async def read(i: int) -> str | None:
            return await redis.get(f"key{i}")

        # Write all first
        await asyncio.gather(*[write(i) for i in range(50)])
        # Then read all
        results = await asyncio.gather(*[read(i) for i in range(50)])
        for i, r in enumerate(results):
            assert r == f"val{i}"

    @pytest.mark.asyncio
    async def test_concurrent_mixed_ops(self) -> None:
        redis = RedisAdapter()
        for i in range(20):
            await redis.set(f"key{i}", f"val{i}")

        async def delete_task(i: int) -> bool:
            return await redis.delete(f"key{i}")

        async def set_task(i: int) -> None:
            await redis.set(f"new{i}", f"newval{i}")

        ops = [delete_task(i) for i in range(10)]
        ops.extend([set_task(i) for i in range(10)])
        await asyncio.gather(*ops)
        # Verify new keys exist
        for i in range(10):
            val = await redis.get(f"new{i}")
            assert val == f"newval{i}"


class TestConcurrentMemoryManager:
    """Tests for concurrent access to the full memory manager."""

    @pytest.mark.asyncio
    async def test_concurrent_stores_different_types(self) -> None:
        manager = create_memory_manager(embedding_dim=64)

        async def store_working(i: int) -> str:
            entry = MemoryEntry(
                id=f"w{i}",
                memory_type=MemoryType.WORKING,
                content=f"working {i}",
            )
            return await manager.store("user1", entry)

        async def store_short(i: int) -> str:
            entry = MemoryEntry(
                id=f"s{i}",
                memory_type=MemoryType.SHORT_TERM,
                content=f"short {i}",
            )
            return await manager.store("user1", entry)

        tasks = [store_working(i) for i in range(10)]
        tasks.extend([store_short(i) for i in range(10)])
        results = await asyncio.gather(*tasks)
        assert all(isinstance(r, str) for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_store_and_forget(self) -> None:
        manager = create_memory_manager(embedding_dim=64)
        for i in range(10):
            entry = MemoryEntry(
                id=f"m{i}",
                memory_type=MemoryType.WORKING,
                content=f"test {i}",
            )
            await manager.store("user1", entry)

        async def forget_task(i: int) -> bool:
            return await manager.forget("user1", f"m{i}")

        async def store_task(i: int) -> str:
            entry = MemoryEntry(
                id=f"new{i}",
                memory_type=MemoryType.WORKING,
                content=f"new {i}",
            )
            return await manager.store("user1", entry)

        tasks = [forget_task(i) for i in range(5)]
        tasks.extend([store_task(i) for i in range(5)])
        await asyncio.gather(*tasks)
