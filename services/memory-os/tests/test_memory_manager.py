"""Unit tests for the Memory Manager (top-level orchestrator)."""

import pytest

from sona_memory.domain.events import (
    MemoryConsolidatedEvent,
    MemoryForgottenEvent,
    MemoryStoredEvent,
)
from sona_memory.domain.models import MemoryEntry, MemoryQuery, MemoryType
from sona_memory.infrastructure.di import create_memory_manager
from sona_memory.infrastructure.memory_manager import MemoryManager


@pytest.fixture
def manager() -> MemoryManager:
    return create_memory_manager(embedding_dim=64)


class TestMemoryManagerStore:
    """Tests for store operations."""

    @pytest.mark.asyncio
    async def test_store_working_memory(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.WORKING,
            content="current thought",
        )
        result_id = await manager.store("user1", entry)
        assert result_id == "m1"

    @pytest.mark.asyncio
    async def test_store_short_term(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m2",
            memory_type=MemoryType.SHORT_TERM,
            content="recent info",
        )
        result_id = await manager.store("user1", entry)
        assert result_id == "m2"

    @pytest.mark.asyncio
    async def test_store_long_term(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m3",
            memory_type=MemoryType.LONG_TERM,
            content="permanent fact",
        )
        result_id = await manager.store("user1", entry)
        assert result_id == "m3"

    @pytest.mark.asyncio
    async def test_store_episodic(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m4",
            memory_type=MemoryType.EPISODIC,
            content="event happened",
        )
        result_id = await manager.store("user1", entry)
        assert result_id == "m4"

    @pytest.mark.asyncio
    async def test_store_semantic(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m5",
            memory_type=MemoryType.SEMANTIC,
            content="fact about world",
        )
        result_id = await manager.store("user1", entry)
        assert result_id == "m5"

    @pytest.mark.asyncio
    async def test_store_generates_id(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="",
            memory_type=MemoryType.WORKING,
            content="test",
        )
        result_id = await manager.store("user1", entry)
        assert result_id != ""
        assert len(result_id) > 0

    @pytest.mark.asyncio
    async def test_store_emits_event(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.WORKING,
            content="test",
        )
        await manager.store("user1", entry)
        events = manager.events
        assert len(events) == 1
        assert isinstance(events[0], MemoryStoredEvent)
        assert events[0].user_id == "user1"
        assert events[0].memory_id == "m1"


class TestMemoryManagerRetrieve:
    """Tests for retrieve operations."""

    @pytest.mark.asyncio
    async def test_retrieve_stored_entry(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.WORKING,
            content="findme",
            importance=0.7,
        )
        await manager.store("user1", entry)
        query = MemoryQuery(
            user_id="user1",
            query="findme",
            memory_types=[MemoryType.WORKING],
        )
        results = await manager.retrieve(query)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_retrieve_empty(self, manager: MemoryManager) -> None:
        query = MemoryQuery(user_id="user1", query="nothing")
        results = await manager.retrieve(query)
        assert results == []


class TestMemoryManagerConsolidate:
    """Tests for consolidation."""

    @pytest.mark.asyncio
    async def test_consolidate(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.SHORT_TERM,
            content="important memory",
            importance=0.9,
        )
        await manager.store("user1", entry)
        count = await manager.consolidate("user1")
        assert count >= 0

    @pytest.mark.asyncio
    async def test_consolidate_emits_event(self, manager: MemoryManager) -> None:
        manager.clear_events()
        await manager.consolidate("user1")
        events = [e for e in manager.events if isinstance(e, MemoryConsolidatedEvent)]
        assert len(events) == 1


class TestMemoryManagerForget:
    """Tests for forget operations."""

    @pytest.mark.asyncio
    async def test_forget_existing(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.WORKING,
            content="forget me",
        )
        await manager.store("user1", entry)
        result = await manager.forget("user1", "m1")
        assert result is True

    @pytest.mark.asyncio
    async def test_forget_nonexistent(self, manager: MemoryManager) -> None:
        result = await manager.forget("user1", "nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_forget_emits_event(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.WORKING,
            content="test",
        )
        await manager.store("user1", entry)
        manager.clear_events()
        await manager.forget("user1", "m1")
        events = [e for e in manager.events if isinstance(e, MemoryForgottenEvent)]
        assert len(events) == 1
        assert events[0].memory_id == "m1"


class TestMemoryManagerMetrics:
    """Tests for metrics tracking."""

    @pytest.mark.asyncio
    async def test_metrics_after_operations(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.WORKING,
            content="test",
        )
        await manager.store("user1", entry)
        await manager.retrieve(MemoryQuery(user_id="user1", query="test"))
        metrics = await manager.get_metrics()
        assert metrics["total_operations"] >= 2


class TestMemoryManagerClearEvents:
    """Tests for event management."""

    @pytest.mark.asyncio
    async def test_clear_events(self, manager: MemoryManager) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.WORKING,
            content="test",
        )
        await manager.store("user1", entry)
        assert len(manager.events) > 0
        manager.clear_events()
        assert len(manager.events) == 0
