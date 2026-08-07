"""Unit tests for the in-memory store implementation."""

from datetime import UTC, datetime, timedelta

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryQuery, MemoryType
from sona_memory.infrastructure.memory_store import InMemoryStore


def _make_entry(
    id: str,
    memory_type: MemoryType = MemoryType.SHORT_TERM,
    content: str = "test",
    importance: float = 0.5,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
    metadata: dict | None = None,
) -> MemoryEntry:
    return MemoryEntry(
        id=id,
        memory_type=memory_type,
        content=content,
        importance=importance,
        created_at=created_at,
        expires_at=expires_at,
        metadata=metadata,
    )


class TestInMemoryStoreBasic:
    """Tests for basic store operations."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self) -> None:
        store = InMemoryStore()
        entry = _make_entry("m1", content="hello")
        await store.store("user1", entry)
        query = MemoryQuery(user_id="user1", query="")
        results = await store.retrieve(query)
        assert len(results) == 1
        assert results[0].content == "hello"

    @pytest.mark.asyncio
    async def test_store_generates_id(self) -> None:
        store = InMemoryStore()
        entry = MemoryEntry(id="", memory_type=MemoryType.WORKING, content="test")
        result_id = await store.store("user1", entry)
        assert result_id != ""
        assert len(result_id) > 0

    @pytest.mark.asyncio
    async def test_store_sets_created_at(self) -> None:
        store = InMemoryStore()
        entry = _make_entry("m1")
        await store.store("user1", entry)
        entries = await store.get_all("user1")
        assert entries[0].created_at is not None

    @pytest.mark.asyncio
    async def test_store_preserves_created_at(self) -> None:
        store = InMemoryStore()
        now = datetime(2024, 1, 1, tzinfo=UTC)
        entry = _make_entry("m1", created_at=now)
        await store.store("user1", entry)
        entries = await store.get_all("user1")
        assert entries[0].created_at == now

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        store = InMemoryStore()
        assert await store.count("user1") == 0
        await store.store("user1", _make_entry("m1"))
        assert await store.count("user1") == 1


class TestInMemoryStoreRetrieve:
    """Tests for retrieve with filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_type(self) -> None:
        store = InMemoryStore()
        await store.store("user1", _make_entry("m1", MemoryType.WORKING))
        await store.store("user1", _make_entry("m2", MemoryType.LONG_TERM))
        query = MemoryQuery(user_id="user1", query="", memory_types=[MemoryType.LONG_TERM])
        results = await store.retrieve(query)
        assert len(results) == 1
        assert results[0].id == "m2"

    @pytest.mark.asyncio
    async def test_filter_by_importance(self) -> None:
        store = InMemoryStore()
        await store.store("user1", _make_entry("low", importance=0.2))
        await store.store("user1", _make_entry("high", importance=0.8))
        query = MemoryQuery(user_id="user1", query="", min_importance=0.5)
        results = await store.retrieve(query)
        assert len(results) == 1
        assert results[0].id == "high"

    @pytest.mark.asyncio
    async def test_filter_by_time_range(self) -> None:
        store = InMemoryStore()
        base = datetime(2024, 1, 15, tzinfo=UTC)
        await store.store("user1", _make_entry("m1", created_at=base))
        await store.store("user1", _make_entry("m2", created_at=base + timedelta(hours=5)))
        query = MemoryQuery(
            user_id="user1",
            query="",
            time_range=(base + timedelta(hours=1), base + timedelta(hours=10)),
        )
        results = await store.retrieve(query)
        assert len(results) == 1
        assert results[0].id == "m2"

    @pytest.mark.asyncio
    async def test_respects_top_k(self) -> None:
        store = InMemoryStore()
        for i in range(10):
            await store.store("user1", _make_entry(f"m{i}"))
        query = MemoryQuery(user_id="user1", query="", top_k=3)
        results = await store.retrieve(query)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_sorted_by_importance(self) -> None:
        store = InMemoryStore()
        await store.store("user1", _make_entry("low", importance=0.2))
        await store.store("user1", _make_entry("high", importance=0.9))
        await store.store("user1", _make_entry("mid", importance=0.5))
        query = MemoryQuery(user_id="user1", query="")
        results = await store.retrieve(query)
        importances = [r.importance for r in results]
        assert importances == sorted(importances, reverse=True)

    @pytest.mark.asyncio
    async def test_filters_expired(self) -> None:
        store = InMemoryStore()
        past = datetime.now(UTC) - timedelta(hours=1)
        await store.store("user1", _make_entry("expired", expires_at=past))
        await store.store("user1", _make_entry("valid"))
        query = MemoryQuery(user_id="user1", query="")
        results = await store.retrieve(query)
        assert len(results) == 1
        assert results[0].id == "valid"


class TestInMemoryStoreConsolidate:
    """Tests for consolidation."""

    @pytest.mark.asyncio
    async def test_promotes_important_short_term(self) -> None:
        store = InMemoryStore()
        await store.store("user1", _make_entry("m1", MemoryType.SHORT_TERM, importance=0.8))
        count = await store.consolidate("user1")
        assert count == 1
        entries = await store.get_all("user1")
        assert entries[0].memory_type == MemoryType.LONG_TERM

    @pytest.mark.asyncio
    async def test_does_not_promote_low_importance(self) -> None:
        store = InMemoryStore()
        await store.store("user1", _make_entry("m1", MemoryType.SHORT_TERM, importance=0.3))
        count = await store.consolidate("user1")
        assert count == 0

    @pytest.mark.asyncio
    async def test_consolidate_removes_expiry(self) -> None:
        store = InMemoryStore()
        future = datetime.now(UTC) + timedelta(hours=24)
        entry = _make_entry("m1", MemoryType.SHORT_TERM, importance=0.9, expires_at=future)
        await store.store("user1", entry)
        await store.consolidate("user1")
        entries = await store.get_all("user1")
        assert entries[0].expires_at is None

    @pytest.mark.asyncio
    async def test_consolidate_empty(self) -> None:
        store = InMemoryStore()
        count = await store.consolidate("user1")
        assert count == 0


class TestInMemoryStoreForget:
    """Tests for forget operation."""

    @pytest.mark.asyncio
    async def test_forget_existing(self) -> None:
        store = InMemoryStore()
        await store.store("user1", _make_entry("m1"))
        assert await store.forget("user1", "m1") is True
        assert await store.count("user1") == 0

    @pytest.mark.asyncio
    async def test_forget_nonexistent(self) -> None:
        store = InMemoryStore()
        assert await store.forget("user1", "m99") is False


class TestInMemoryStoreConversation:
    """Tests for conversation history."""

    @pytest.mark.asyncio
    async def test_get_conversation_history(self) -> None:
        store = InMemoryStore()
        now = datetime.now(UTC)
        entry = MemoryEntry(
            id="c1",
            memory_type=MemoryType.WORKING,
            content="hello",
            metadata={"session_id": "sess1"},
            created_at=now,
        )
        await store.store("user1", entry)
        history = await store.get_conversation_history("sess1")
        assert len(history) == 1
        assert history[0].content == "hello"

    @pytest.mark.asyncio
    async def test_conversation_limit(self) -> None:
        store = InMemoryStore()
        now = datetime.now(UTC)
        for i in range(60):
            entry = MemoryEntry(
                id=f"c{i}",
                memory_type=MemoryType.WORKING,
                content=f"msg {i}",
                metadata={"session_id": "sess1"},
                created_at=now + timedelta(seconds=i),
            )
            await store.store("user1", entry)
        history = await store.get_conversation_history("sess1", limit=10)
        assert len(history) == 10

    @pytest.mark.asyncio
    async def test_conversation_filters_by_session(self) -> None:
        store = InMemoryStore()
        now = datetime.now(UTC)
        await store.store(
            "user1",
            MemoryEntry(
                id="c1",
                memory_type=MemoryType.WORKING,
                content="a",
                metadata={"session_id": "s1"},
                created_at=now,
            ),
        )
        await store.store(
            "user1",
            MemoryEntry(
                id="c2",
                memory_type=MemoryType.WORKING,
                content="b",
                metadata={"session_id": "s2"},
                created_at=now,
            ),
        )
        history = await store.get_conversation_history("s1")
        assert len(history) == 1
        assert history[0].id == "c1"
