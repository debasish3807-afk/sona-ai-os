"""Unit tests for THALAMUS domain events."""

from dataclasses import FrozenInstanceError

import pytest
from sona_thalamus.domain.events import (
    ExecutionPlanCreatedEvent,
    IntentClassifiedEvent,
    RoutingFailedEvent,
)

from sona_shared.domain.primitives import DomainEvent


class TestIntentClassifiedEvent:
    """Tests for IntentClassifiedEvent."""

    def test_creation(self) -> None:
        """Test creating an IntentClassifiedEvent."""
        event = IntentClassifiedEvent(
            content="Write code",
            intent="code",
            confidence=0.85,
        )
        assert event.content == "Write code"
        assert event.intent == "code"
        assert event.confidence == 0.85

    def test_default_values(self) -> None:
        """Test default values are empty/zero."""
        event = IntentClassifiedEvent()
        assert event.content == ""
        assert event.intent == ""
        assert event.confidence == 0.0

    def test_is_domain_event(self) -> None:
        """Test that it inherits from DomainEvent."""
        event = IntentClassifiedEvent()
        assert isinstance(event, DomainEvent)

    def test_has_event_id(self) -> None:
        """Test that event has an auto-generated event_id."""
        event = IntentClassifiedEvent()
        assert event.event_id is not None

    def test_is_frozen(self) -> None:
        """Test immutability."""
        event = IntentClassifiedEvent(content="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.content = "other"  # type: ignore[misc]


class TestExecutionPlanCreatedEvent:
    """Tests for ExecutionPlanCreatedEvent."""

    def test_creation(self) -> None:
        """Test creating an ExecutionPlanCreatedEvent."""
        event = ExecutionPlanCreatedEvent(
            plan_id="plan-123",
            intent="code",
            model_id="codellama",
            steps_count=3,
        )
        assert event.plan_id == "plan-123"
        assert event.intent == "code"
        assert event.model_id == "codellama"
        assert event.steps_count == 3

    def test_default_values(self) -> None:
        """Test default values."""
        event = ExecutionPlanCreatedEvent()
        assert event.plan_id == ""
        assert event.intent == ""
        assert event.model_id == ""
        assert event.steps_count == 0

    def test_is_domain_event(self) -> None:
        """Test inheritance."""
        event = ExecutionPlanCreatedEvent()
        assert isinstance(event, DomainEvent)

    def test_has_occurred_at(self) -> None:
        """Test that event has a timestamp."""
        event = ExecutionPlanCreatedEvent()
        assert event.occurred_at is not None


class TestRoutingFailedEvent:
    """Tests for RoutingFailedEvent."""

    def test_creation(self) -> None:
        """Test creating a RoutingFailedEvent."""
        event = RoutingFailedEvent(
            content="Hello",
            error="Timeout occurred",
        )
        assert event.content == "Hello"
        assert event.error == "Timeout occurred"

    def test_default_values(self) -> None:
        """Test default values."""
        event = RoutingFailedEvent()
        assert event.content == ""
        assert event.error == ""

    def test_is_domain_event(self) -> None:
        """Test inheritance."""
        event = RoutingFailedEvent()
        assert isinstance(event, DomainEvent)

    def test_is_frozen(self) -> None:
        """Test immutability."""
        event = RoutingFailedEvent(error="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.error = "other"  # type: ignore[misc]
