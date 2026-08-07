"""Unit tests for episodic memory manager."""

from datetime import UTC, datetime, timedelta

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.episodic_memory import EpisodicConfig, EpisodicMemory


def _make_entry(
    id: str,
    content: str = "event",
    created_at: datetime | None = None,
    tags: tuple[str, ...] = (),
    metadata: dict | None = None,
) -> MemoryEntry:
    return MemoryEntry(
        id=id,
        memory_type=MemoryType.EPISODIC,
        content=content,
        created_at=created_at,
        tags=tags,
        metadata=metadata,
    )


class TestEpisodicStore:
    """Tests for storing episodic memories."""

    @pytest.mark.asyncio
    async def test_store_and_get(self) -> None:
        em = EpisodicMemory()
        entry = _make_entry("e1", "meeting at 3pm")
        await em.store("user1", entry)
        result = await em.get("user1", "e1")
        assert result is not None
        assert result.content == "meeting at 3pm"

    @pytest.mark.asyncio
    async def test_store_forces_episodic_type(self) -> None:
        em = EpisodicMemory()
        entry = MemoryEntry(id="e1", memory_type=MemoryType.WORKING, content="event")
        await em.store("user1", entry)
        result = await em.get("user1", "e1")
        assert result is not None
        assert result.memory_type == MemoryType.EPISODIC

    @pytest.mark.asyncio
    async def test_store_sets_default_importance(self) -> None:
        config = EpisodicConfig(default_importance=0.6)
        em = EpisodicMemory(config=config)
        entry = _make_entry("e1")  # importance defaults to 0.5
        await em.store("user1", entry)
        result = await em.get("user1", "e1")
        assert result is not None
        assert result.importance == 0.6

    @pytest.mark.asyncio
    async def test_store_returns_id(self) -> None:
        em = EpisodicMemory()
        result_id = await em.store("user1", _make_entry("e1"))
        assert result_id == "e1"


class TestEpisodicTimeRange:
    """Tests for time-based queries."""

    @pytest.mark.asyncio
    async def test_get_by_time_range(self) -> None:
        em = EpisodicMemory()
        base = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        await em.store("user1", _make_entry("e1", created_at=base))
        await em.store("user1", _make_entry("e2", created_at=base + timedelta(hours=2)))
        await em.store("user1", _make_entry("e3", created_at=base + timedelta(hours=5)))

        results = await em.get_by_time_range(
            "user1",
            base + timedelta(hours=1),
            base + timedelta(hours=4),
        )
        assert len(results) == 1
        assert results[0].id == "e2"

    @pytest.mark.asyncio
    async def test_get_by_time_range_empty(self) -> None:
        em = EpisodicMemory()
        now = datetime.now(UTC)
        results = await em.get_by_time_range("user1", now, now + timedelta(hours=1))
        assert results == []

    @pytest.mark.asyncio
    async def test_entries_sorted_by_time(self) -> None:
        em = EpisodicMemory()
        base = datetime(2024, 1, 1, tzinfo=UTC)
        # Insert out of order
        await em.store("user1", _make_entry("e2", created_at=base + timedelta(hours=2)))
        await em.store("user1", _make_entry("e1", created_at=base + timedelta(hours=1)))
        all_entries = await em.get_all("user1")
        assert all_entries[0].id == "e1"
        assert all_entries[1].id == "e2"


class TestEpisodicRelated:
    """Tests for related episode links."""

    @pytest.mark.asyncio
    async def test_get_related(self) -> None:
        em = EpisodicMemory()
        now = datetime.now(UTC)
        e1 = _make_entry("e1", created_at=now, metadata={"related_episodes": ["e2"]})
        e2 = _make_entry("e2", created_at=now)
        await em.store("user1", e1)
        await em.store("user1", e2)
        related = await em.get_related("user1", "e1")
        assert len(related) == 1
        assert related[0].id == "e2"

    @pytest.mark.asyncio
    async def test_get_related_bidirectional(self) -> None:
        em = EpisodicMemory()
        now = datetime.now(UTC)
        e1 = _make_entry("e1", created_at=now)
        e2 = _make_entry("e2", created_at=now, metadata={"related_episodes": ["e1"]})
        await em.store("user1", e1)
        await em.store("user1", e2)
        related = await em.get_related("user1", "e1")
        assert len(related) == 1
        assert related[0].id == "e2"

    @pytest.mark.asyncio
    async def test_get_related_nonexistent(self) -> None:
        em = EpisodicMemory()
        related = await em.get_related("user1", "no")
        assert related == []


class TestEpisodicOperations:
    """Tests for various operations."""

    @pytest.mark.asyncio
    async def test_get_recent(self) -> None:
        em = EpisodicMemory()
        base = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(5):
            await em.store("user1", _make_entry(f"e{i}", created_at=base + timedelta(hours=i)))
        recent = await em.get_recent("user1", limit=2)
        assert len(recent) == 2
        assert recent[0].id == "e4"

    @pytest.mark.asyncio
    async def test_get_by_tags(self) -> None:
        em = EpisodicMemory()
        now = datetime.now(UTC)
        await em.store("user1", _make_entry("e1", created_at=now, tags=("meeting",)))
        await em.store("user1", _make_entry("e2", created_at=now, tags=("lunch",)))
        results = await em.get_by_tags("user1", {"meeting"})
        assert len(results) == 1
        assert results[0].id == "e1"

    @pytest.mark.asyncio
    async def test_remove(self) -> None:
        em = EpisodicMemory()
        await em.store("user1", _make_entry("e1", created_at=datetime.now(UTC)))
        assert await em.remove("user1", "e1") is True
        assert await em.get("user1", "e1") is None

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        em = EpisodicMemory()
        assert await em.count("user1") == 0
        await em.store("user1", _make_entry("e1", created_at=datetime.now(UTC)))
        assert await em.count("user1") == 1

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        em = EpisodicMemory()
        await em.store("user1", _make_entry("e1", created_at=datetime.now(UTC)))
        count = await em.clear("user1")
        assert count == 1
        assert await em.count("user1") == 0

    @pytest.mark.asyncio
    async def test_capacity_eviction(self) -> None:
        config = EpisodicConfig(max_capacity_per_user=5)
        em = EpisodicMemory(config=config)
        base = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(10):
            await em.store("user1", _make_entry(f"e{i}", created_at=base + timedelta(hours=i)))
        assert await em.count("user1") == 5
