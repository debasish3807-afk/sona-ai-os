"""Unit tests for conversation memory manager."""

from datetime import UTC, datetime, timedelta

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.conversation_memory import (
    ConversationConfig,
    ConversationMemory,
)


def _make_msg(id: str, content: str = "hi", created_at: datetime | None = None) -> MemoryEntry:
    return MemoryEntry(
        id=id, memory_type=MemoryType.WORKING, content=content, created_at=created_at
    )


class TestConversationAdd:
    """Tests for adding messages."""

    @pytest.mark.asyncio
    async def test_add_and_get_history(self) -> None:
        cm = ConversationMemory()
        await cm.add_message("user1", "session1", _make_msg("m1", "hello"))
        await cm.add_message("user1", "session1", _make_msg("m2", "world"))
        history = await cm.get_history("user1", "session1")
        assert len(history) == 2
        assert history[0].content == "hello"
        assert history[1].content == "world"

    @pytest.mark.asyncio
    async def test_add_returns_id(self) -> None:
        cm = ConversationMemory()
        result = await cm.add_message("user1", "s1", _make_msg("m1"))
        assert result == "m1"

    @pytest.mark.asyncio
    async def test_add_sets_session_metadata(self) -> None:
        cm = ConversationMemory()
        await cm.add_message("user1", "s1", _make_msg("m1"))
        history = await cm.get_history("user1", "s1")
        assert history[0].metadata is not None
        assert history[0].metadata["session_id"] == "s1"

    @pytest.mark.asyncio
    async def test_add_forces_working_type(self) -> None:
        cm = ConversationMemory()
        entry = MemoryEntry(id="m1", memory_type=MemoryType.LONG_TERM, content="test")
        await cm.add_message("user1", "s1", entry)
        history = await cm.get_history("user1", "s1")
        assert history[0].memory_type == MemoryType.WORKING


class TestConversationRingBuffer:
    """Tests for ring buffer behavior."""

    @pytest.mark.asyncio
    async def test_ring_buffer_limit(self) -> None:
        config = ConversationConfig(max_messages_per_session=5)
        cm = ConversationMemory(config=config)
        for i in range(10):
            await cm.add_message("user1", "s1", _make_msg(f"m{i}", f"msg {i}"))
        history = await cm.get_history("user1", "s1")
        assert len(history) == 5
        # Oldest messages should be dropped
        assert history[0].content == "msg 5"

    @pytest.mark.asyncio
    async def test_session_limit(self) -> None:
        config = ConversationConfig(max_sessions_per_user=3)
        cm = ConversationMemory(config=config)
        for i in range(5):
            await cm.add_message("user1", f"s{i}", _make_msg(f"m{i}"))
        sessions = await cm.get_sessions("user1")
        assert len(sessions) <= 3


class TestConversationRetrieval:
    """Tests for retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_recent(self) -> None:
        cm = ConversationMemory()
        for i in range(10):
            await cm.add_message("user1", "s1", _make_msg(f"m{i}", f"msg {i}"))
        recent = await cm.get_recent("user1", "s1", limit=3)
        assert len(recent) == 3
        assert recent[-1].content == "msg 9"

    @pytest.mark.asyncio
    async def test_get_history_with_limit(self) -> None:
        cm = ConversationMemory()
        for i in range(10):
            await cm.add_message("user1", "s1", _make_msg(f"m{i}"))
        history = await cm.get_history("user1", "s1", limit=5)
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_get_history_empty(self) -> None:
        cm = ConversationMemory()
        history = await cm.get_history("user1", "s1")
        assert history == []

    @pytest.mark.asyncio
    async def test_get_sessions(self) -> None:
        cm = ConversationMemory()
        await cm.add_message("user1", "s1", _make_msg("m1"))
        await cm.add_message("user1", "s2", _make_msg("m2"))
        sessions = await cm.get_sessions("user1")
        assert set(sessions) == {"s1", "s2"}

    @pytest.mark.asyncio
    async def test_session_length(self) -> None:
        cm = ConversationMemory()
        await cm.add_message("user1", "s1", _make_msg("m1"))
        await cm.add_message("user1", "s1", _make_msg("m2"))
        assert await cm.session_length("user1", "s1") == 2

    @pytest.mark.asyncio
    async def test_find_by_content(self) -> None:
        cm = ConversationMemory()
        await cm.add_message("user1", "s1", _make_msg("m1", "hello world"))
        await cm.add_message("user1", "s1", _make_msg("m2", "goodbye"))
        results = await cm.find_by_content("user1", "s1", "hello")
        assert len(results) == 1
        assert results[0].id == "m1"

    @pytest.mark.asyncio
    async def test_get_messages_after(self) -> None:
        cm = ConversationMemory()
        base = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        await cm.add_message("user1", "s1", _make_msg("m1", created_at=base))
        await cm.add_message("user1", "s1", _make_msg("m2", created_at=base + timedelta(hours=2)))
        results = await cm.get_messages_after("user1", "s1", base + timedelta(hours=1))
        assert len(results) == 1
        assert results[0].id == "m2"


class TestConversationCleanup:
    """Tests for clearing sessions."""

    @pytest.mark.asyncio
    async def test_clear_session(self) -> None:
        cm = ConversationMemory()
        await cm.add_message("user1", "s1", _make_msg("m1"))
        count = await cm.clear_session("user1", "s1")
        assert count == 1
        assert await cm.session_length("user1", "s1") == 0

    @pytest.mark.asyncio
    async def test_clear_user(self) -> None:
        cm = ConversationMemory()
        await cm.add_message("user1", "s1", _make_msg("m1"))
        await cm.add_message("user1", "s2", _make_msg("m2"))
        count = await cm.clear_user("user1")
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_all_messages(self) -> None:
        cm = ConversationMemory()
        await cm.add_message("user1", "s1", _make_msg("m1"))
        await cm.add_message("user1", "s2", _make_msg("m2"))
        all_msgs = await cm.get_all_messages("user1")
        assert len(all_msgs) == 2
