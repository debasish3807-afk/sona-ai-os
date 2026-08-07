"""Unit tests for memory cleanup service."""

import asyncio

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.cleanup import CleanupConfig, CleanupService
from sona_memory.infrastructure.short_term_memory import ShortTermConfig, ShortTermMemory
from sona_memory.infrastructure.working_memory import WorkingMemoryConfig, WorkingMemoryManager


def _make_entry(id: str, importance: float = 0.5) -> MemoryEntry:
    return MemoryEntry(id=id, memory_type=MemoryType.WORKING, content="test", importance=importance)


class TestCleanupUser:
    """Tests for per-user cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_working_memory(self) -> None:
        wm_config = WorkingMemoryConfig(max_capacity=100, ttl_seconds=0)
        wm = WorkingMemoryManager(config=wm_config)
        stm = ShortTermMemory()
        cleanup = CleanupService(working_memory=wm, short_term=stm)

        await wm.store("user1", _make_entry("m1"))
        await asyncio.sleep(0.01)

        cleaned = await cleanup.cleanup_user("user1")
        assert cleaned >= 1

    @pytest.mark.asyncio
    async def test_cleanup_expired_short_term(self) -> None:
        wm = WorkingMemoryManager()
        stm_config = ShortTermConfig(max_capacity=100, ttl_seconds=0)
        stm = ShortTermMemory(config=stm_config)
        cleanup = CleanupService(working_memory=wm, short_term=stm)

        await stm.store(
            "user1", MemoryEntry(id="m1", memory_type=MemoryType.SHORT_TERM, content="test")
        )
        await asyncio.sleep(0.01)

        cleaned = await cleanup.cleanup_user("user1")
        assert cleaned >= 1

    @pytest.mark.asyncio
    async def test_cleanup_no_expired(self) -> None:
        wm = WorkingMemoryManager()
        stm = ShortTermMemory()
        cleanup = CleanupService(working_memory=wm, short_term=stm)

        await wm.store("user1", _make_entry("m1"))
        cleaned = await cleanup.cleanup_user("user1")
        assert cleaned == 0

    @pytest.mark.asyncio
    async def test_cleanup_empty_user(self) -> None:
        wm = WorkingMemoryManager()
        stm = ShortTermMemory()
        cleanup = CleanupService(working_memory=wm, short_term=stm)
        cleaned = await cleanup.cleanup_user("user1")
        assert cleaned == 0


class TestCleanupAllUsers:
    """Tests for multi-user cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_multiple_users(self) -> None:
        wm_config = WorkingMemoryConfig(max_capacity=100, ttl_seconds=0)
        wm = WorkingMemoryManager(config=wm_config)
        stm = ShortTermMemory()
        cleanup = CleanupService(working_memory=wm, short_term=stm)

        await wm.store("user1", _make_entry("m1"))
        await wm.store("user2", _make_entry("m2"))
        await asyncio.sleep(0.01)

        total = await cleanup.cleanup_all_users(["user1", "user2"])
        assert total >= 2


class TestEvictLowImportance:
    """Tests for importance-based eviction."""

    @pytest.mark.asyncio
    async def test_evicts_least_important(self) -> None:
        wm = WorkingMemoryManager()
        stm = ShortTermMemory()
        cleanup = CleanupService(working_memory=wm, short_term=stm)

        await stm.store(
            "user1",
            MemoryEntry(
                id="low",
                memory_type=MemoryType.SHORT_TERM,
                content="t",
                importance=0.1,
            ),
        )
        await stm.store(
            "user1",
            MemoryEntry(
                id="mid",
                memory_type=MemoryType.SHORT_TERM,
                content="t",
                importance=0.5,
            ),
        )
        await stm.store(
            "user1",
            MemoryEntry(
                id="high",
                memory_type=MemoryType.SHORT_TERM,
                content="t",
                importance=0.9,
            ),
        )

        evicted = await cleanup.evict_low_importance("user1", target_reduction=2)
        assert evicted == 2
        remaining = await stm.get_all("user1")
        assert len(remaining) == 1
        assert remaining[0].id == "high"

    @pytest.mark.asyncio
    async def test_evict_empty(self) -> None:
        wm = WorkingMemoryManager()
        stm = ShortTermMemory()
        cleanup = CleanupService(working_memory=wm, short_term=stm)
        evicted = await cleanup.evict_low_importance("user1")
        assert evicted == 0


class TestBackgroundCleanup:
    """Tests for background cleanup task."""

    @pytest.mark.asyncio
    async def test_start_and_stop(self) -> None:
        wm = WorkingMemoryManager()
        stm = ShortTermMemory()
        config = CleanupConfig(cleanup_interval_seconds=0.05)
        cleanup = CleanupService(working_memory=wm, short_term=stm, config=config)

        cleanup.start_background_cleanup(["user1"])
        assert cleanup.is_running is True
        await asyncio.sleep(0.1)
        await cleanup.stop_background_cleanup()
        assert cleanup.is_running is False

    @pytest.mark.asyncio
    async def test_no_double_start(self) -> None:
        wm = WorkingMemoryManager()
        stm = ShortTermMemory()
        config = CleanupConfig(cleanup_interval_seconds=0.1)
        cleanup = CleanupService(working_memory=wm, short_term=stm, config=config)

        cleanup.start_background_cleanup(["user1"])
        cleanup.start_background_cleanup(["user1"])  # should be no-op
        assert cleanup.is_running is True
        await cleanup.stop_background_cleanup()

    @pytest.mark.asyncio
    async def test_config_accessible(self) -> None:
        wm = WorkingMemoryManager()
        stm = ShortTermMemory()
        config = CleanupConfig(cleanup_interval_seconds=30.0)
        cleanup = CleanupService(working_memory=wm, short_term=stm, config=config)
        assert cleanup.config.cleanup_interval_seconds == 30.0
