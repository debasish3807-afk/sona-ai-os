"""Unit tests for Memory OS domain events."""

from dataclasses import FrozenInstanceError

import pytest

from sona_memory.domain.events import (
    MemoryConsolidatedEvent,
    MemoryExpiredEvent,
    MemoryForgottenEvent,
    MemoryRetrievedEvent,
    MemoryStoredEvent,
)
from sona_shared.domain.primitives import DomainEvent


class TestMemoryStoredEvent:
    """Tests for MemoryStoredEvent."""

    def test_creation_with_defaults(self) -> None:
        event = MemoryStoredEvent()
        assert event.user_id == ""
        assert event.memory_id == ""
        assert event.memory_type == ""
        assert event.importance == 0.0

    def test_creation_with_values(self) -> None:
        event = MemoryStoredEvent(
            user_id="user-1",
            memory_id="mem-1",
            memory_type="working",
            importance=0.9,
        )
        assert event.user_id == "user-1"
        assert event.memory_id == "mem-1"
        assert event.memory_type == "working"
        assert event.importance == 0.9

    def test_is_domain_event(self) -> None:
        event = MemoryStoredEvent()
        assert isinstance(event, DomainEvent)

    def test_has_event_id(self) -> None:
        event = MemoryStoredEvent()
        assert event.event_id is not None

    def test_has_occurred_at(self) -> None:
        event = MemoryStoredEvent()
        assert event.occurred_at is not None

    def test_is_frozen(self) -> None:
        event = MemoryStoredEvent(user_id="user-1")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.user_id = "changed"  # type: ignore[misc]

    def test_unique_event_ids(self) -> None:
        e1 = MemoryStoredEvent()
        e2 = MemoryStoredEvent()
        assert e1.event_id != e2.event_id


class TestMemoryRetrievedEvent:
    """Tests for MemoryRetrievedEvent."""

    def test_creation_with_defaults(self) -> None:
        event = MemoryRetrievedEvent()
        assert event.user_id == ""
        assert event.query == ""
        assert event.results_count == 0

    def test_creation_with_values(self) -> None:
        event = MemoryRetrievedEvent(
            user_id="user-2",
            query="weather today",
            results_count=5,
        )
        assert event.user_id == "user-2"
        assert event.query == "weather today"
        assert event.results_count == 5

    def test_is_domain_event(self) -> None:
        event = MemoryRetrievedEvent()
        assert isinstance(event, DomainEvent)

    def test_is_frozen(self) -> None:
        event = MemoryRetrievedEvent(results_count=3)
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.results_count = 10  # type: ignore[misc]


class TestMemoryConsolidatedEvent:
    """Tests for MemoryConsolidatedEvent."""

    def test_creation_with_defaults(self) -> None:
        event = MemoryConsolidatedEvent()
        assert event.user_id == ""
        assert event.consolidated_count == 0

    def test_creation_with_values(self) -> None:
        event = MemoryConsolidatedEvent(
            user_id="user-3",
            consolidated_count=7,
        )
        assert event.user_id == "user-3"
        assert event.consolidated_count == 7

    def test_is_domain_event(self) -> None:
        event = MemoryConsolidatedEvent()
        assert isinstance(event, DomainEvent)


class TestMemoryForgottenEvent:
    """Tests for MemoryForgottenEvent."""

    def test_creation_with_defaults(self) -> None:
        event = MemoryForgottenEvent()
        assert event.user_id == ""
        assert event.memory_id == ""

    def test_creation_with_values(self) -> None:
        event = MemoryForgottenEvent(
            user_id="user-4",
            memory_id="mem-42",
        )
        assert event.user_id == "user-4"
        assert event.memory_id == "mem-42"

    def test_is_domain_event(self) -> None:
        event = MemoryForgottenEvent()
        assert isinstance(event, DomainEvent)


class TestMemoryExpiredEvent:
    """Tests for MemoryExpiredEvent."""

    def test_creation_with_defaults(self) -> None:
        event = MemoryExpiredEvent()
        assert event.user_id == ""
        assert event.expired_count == 0

    def test_creation_with_values(self) -> None:
        event = MemoryExpiredEvent(
            user_id="user-5",
            expired_count=12,
        )
        assert event.user_id == "user-5"
        assert event.expired_count == 12

    def test_is_domain_event(self) -> None:
        event = MemoryExpiredEvent()
        assert isinstance(event, DomainEvent)

    def test_is_frozen(self) -> None:
        event = MemoryExpiredEvent(expired_count=5)
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.expired_count = 0  # type: ignore[misc]
