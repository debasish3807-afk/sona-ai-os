"""Unit tests for Memory OS domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest
from domain.models import MemoryEntry, MemoryQuery, MemoryType


class TestMemoryType:
    """Tests for the MemoryType enum."""

    def test_all_types_defined(self) -> None:
        """Verify all expected memory types are available."""
        assert MemoryType.WORKING == "working"
        assert MemoryType.SHORT_TERM == "short_term"
        assert MemoryType.LONG_TERM == "long_term"
        assert MemoryType.EPISODIC == "episodic"
        assert MemoryType.SEMANTIC == "semantic"

    def test_type_count(self) -> None:
        """Verify exactly 5 memory types exist."""
        assert len(MemoryType) == 5

    def test_type_is_str_enum(self) -> None:
        """Verify memory types are usable as strings."""
        assert str(MemoryType.WORKING) == "working"
        assert str(MemoryType.LONG_TERM) == "long_term"


class TestMemoryEntry:
    """Tests for the MemoryEntry frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        entry = MemoryEntry(
            id="mem-001",
            memory_type=MemoryType.WORKING,
            content="User asked about weather",
        )
        assert entry.id == "mem-001"
        assert entry.memory_type == MemoryType.WORKING
        assert entry.content == "User asked about weather"

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        entry = MemoryEntry(
            id="mem-002",
            memory_type=MemoryType.SHORT_TERM,
            content="test content",
        )
        assert entry.embedding is None
        assert entry.metadata is None
        assert entry.importance == 0.5
        assert entry.created_at is None
        assert entry.expires_at is None
        assert entry.tags == ()

    def test_custom_values(self) -> None:
        """Create with all optional fields."""
        now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        expires = now + timedelta(hours=24)
        entry = MemoryEntry(
            id="mem-003",
            memory_type=MemoryType.LONG_TERM,
            content="Important user preference",
            embedding=[0.1, 0.2, 0.3, 0.4],
            metadata={"source": "conversation", "topic": "preferences"},
            importance=0.9,
            created_at=now,
            expires_at=expires,
            tags=("preference", "important"),
        )
        assert entry.embedding == [0.1, 0.2, 0.3, 0.4]
        assert entry.metadata == {"source": "conversation", "topic": "preferences"}
        assert entry.importance == 0.9
        assert entry.created_at == now
        assert entry.expires_at == expires
        assert entry.tags == ("preference", "important")

    def test_is_frozen(self) -> None:
        """Verify MemoryEntry is immutable."""
        entry = MemoryEntry(
            id="mem-004",
            memory_type=MemoryType.EPISODIC,
            content="Something happened",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            entry.content = "changed"  # type: ignore[misc]

    def test_episodic_memory_type(self) -> None:
        """Create an episodic memory entry."""
        entry = MemoryEntry(
            id="mem-005",
            memory_type=MemoryType.EPISODIC,
            content="User had a meeting at 3pm",
            importance=0.7,
            tags=("event", "calendar"),
        )
        assert entry.memory_type == MemoryType.EPISODIC
        assert entry.importance == 0.7

    def test_semantic_memory_type(self) -> None:
        """Create a semantic memory entry."""
        entry = MemoryEntry(
            id="mem-006",
            memory_type=MemoryType.SEMANTIC,
            content="Python is a programming language",
            embedding=[0.5] * 128,
            importance=0.8,
        )
        assert entry.memory_type == MemoryType.SEMANTIC
        assert len(entry.embedding) == 128


class TestMemoryQuery:
    """Tests for the MemoryQuery frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        query = MemoryQuery(
            user_id="user-123",
            query="What did we discuss yesterday?",
        )
        assert query.user_id == "user-123"
        assert query.query == "What did we discuss yesterday?"

    def test_default_values(self) -> None:
        """Verify default values."""
        query = MemoryQuery(user_id="u1", query="test")
        assert query.memory_types is None
        assert query.top_k == 10
        assert query.min_importance == 0.0
        assert query.time_range is None

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        start = datetime(2024, 1, 1, tzinfo=UTC)
        end = datetime(2024, 1, 31, tzinfo=UTC)
        query = MemoryQuery(
            user_id="user-456",
            query="important conversations",
            memory_types=[MemoryType.LONG_TERM, MemoryType.EPISODIC],
            top_k=5,
            min_importance=0.7,
            time_range=(start, end),
        )
        assert query.memory_types == [MemoryType.LONG_TERM, MemoryType.EPISODIC]
        assert query.top_k == 5
        assert query.min_importance == 0.7
        assert query.time_range == (start, end)

    def test_is_frozen(self) -> None:
        """Verify MemoryQuery is immutable."""
        query = MemoryQuery(user_id="u1", query="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            query.query = "changed"  # type: ignore[misc]

    def test_single_memory_type_filter(self) -> None:
        """Query with a single memory type filter."""
        query = MemoryQuery(
            user_id="u1",
            query="search working memory",
            memory_types=[MemoryType.WORKING],
        )
        assert query.memory_types == [MemoryType.WORKING]
        assert len(query.memory_types) == 1
