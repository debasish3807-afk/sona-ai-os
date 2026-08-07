"""Tests for Brain OS domain events.

Tests verify that domain events are correctly defined, immutable,
and carry the expected data.
"""

import pytest

from sona_brain.domain.events import (
    ExecutionCompletedEvent,
    ExecutionFailedEvent,
    ExecutionStartedEvent,
    StepCompletedEvent,
    StepFailedEvent,
)
from sona_shared.domain.primitives import DomainEvent


class TestExecutionStartedEvent:
    """Tests for ExecutionStartedEvent."""

    def test_creation_with_defaults(self) -> None:
        """Create event with default values."""
        event = ExecutionStartedEvent()
        assert event.plan_id == ""
        assert event.intent == ""
        assert event.steps_count == 0

    def test_creation_with_values(self) -> None:
        """Create event with specific values."""
        event = ExecutionStartedEvent(
            plan_id="plan-123",
            intent="code_generation",
            steps_count=5,
        )
        assert event.plan_id == "plan-123"
        assert event.intent == "code_generation"
        assert event.steps_count == 5

    def test_is_domain_event(self) -> None:
        """Verify event inherits from DomainEvent."""
        event = ExecutionStartedEvent(plan_id="p1")
        assert isinstance(event, DomainEvent)

    def test_is_frozen(self) -> None:
        """Verify event is immutable."""
        event = ExecutionStartedEvent(plan_id="p1")
        with pytest.raises(AttributeError):
            event.plan_id = "changed"  # type: ignore[misc]

    def test_has_event_id(self) -> None:
        """Verify event has an event_id from DomainEvent."""
        event = ExecutionStartedEvent()
        assert event.event_id is not None

    def test_has_occurred_at(self) -> None:
        """Verify event has occurred_at timestamp."""
        event = ExecutionStartedEvent()
        assert event.occurred_at is not None


class TestStepCompletedEvent:
    """Tests for StepCompletedEvent."""

    def test_creation(self) -> None:
        """Create step completed event."""
        event = StepCompletedEvent(
            plan_id="plan-1",
            step_id="step-a",
            step_type="llm_call",
            latency_ms=250.0,
        )
        assert event.plan_id == "plan-1"
        assert event.step_id == "step-a"
        assert event.step_type == "llm_call"
        assert event.latency_ms == 250.0

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        event = StepCompletedEvent(plan_id="p1", step_id="s1")
        with pytest.raises(AttributeError):
            event.step_id = "changed"  # type: ignore[misc]


class TestStepFailedEvent:
    """Tests for StepFailedEvent."""

    def test_creation(self) -> None:
        """Create step failed event."""
        event = StepFailedEvent(
            plan_id="plan-1",
            step_id="step-b",
            error="Connection refused",
            retryable=True,
        )
        assert event.plan_id == "plan-1"
        assert event.step_id == "step-b"
        assert event.error == "Connection refused"
        assert event.retryable is True

    def test_defaults(self) -> None:
        """Verify default values."""
        event = StepFailedEvent()
        assert event.retryable is False
        assert event.error == ""


class TestExecutionCompletedEvent:
    """Tests for ExecutionCompletedEvent."""

    def test_creation(self) -> None:
        """Create execution completed event."""
        event = ExecutionCompletedEvent(
            plan_id="plan-1",
            total_latency_ms=1500.0,
            tokens_in=200,
            tokens_out=100,
        )
        assert event.plan_id == "plan-1"
        assert event.total_latency_ms == 1500.0
        assert event.tokens_in == 200
        assert event.tokens_out == 100

    def test_is_domain_event(self) -> None:
        """Verify inherits DomainEvent."""
        event = ExecutionCompletedEvent()
        assert isinstance(event, DomainEvent)


class TestExecutionFailedEvent:
    """Tests for ExecutionFailedEvent."""

    def test_creation(self) -> None:
        """Create execution failed event."""
        event = ExecutionFailedEvent(
            plan_id="plan-1",
            error="All retries exhausted",
            steps_completed=3,
        )
        assert event.plan_id == "plan-1"
        assert event.error == "All retries exhausted"
        assert event.steps_completed == 3

    def test_defaults(self) -> None:
        """Verify default values."""
        event = ExecutionFailedEvent()
        assert event.plan_id == ""
        assert event.error == ""
        assert event.steps_completed == 0

    def test_is_frozen(self) -> None:
        """Verify immutability."""
        event = ExecutionFailedEvent(plan_id="p1")
        with pytest.raises(AttributeError):
            event.error = "changed"  # type: ignore[misc]
