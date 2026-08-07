"""Unit tests for AI Kernel domain events.

Tests verify that domain events are correctly structured,
carry the right data, and inherit from DomainEvent properly.
"""

import pytest

from sona_ai_kernel.domain.events import (
    InferenceCompletedEvent,
    InferenceFailedEvent,
    InferenceStartedEvent,
    ProviderHealthChangedEvent,
)
from sona_shared.domain.primitives import DomainEvent


class TestInferenceStartedEvent:
    """Tests for InferenceStartedEvent."""

    def test_is_domain_event(self) -> None:
        """Verify event inherits from DomainEvent."""
        event = InferenceStartedEvent(
            request_id="req-1",
            provider="ollama",
            model_id="llama3.2",
        )
        assert isinstance(event, DomainEvent)

    def test_fields_set_correctly(self) -> None:
        """Verify all fields are stored correctly."""
        event = InferenceStartedEvent(
            request_id="req-123",
            provider="openai",
            model_id="gpt-4o",
        )
        assert event.request_id == "req-123"
        assert event.provider == "openai"
        assert event.model_id == "gpt-4o"

    def test_default_values(self) -> None:
        """Verify defaults work for optional-like fields."""
        event = InferenceStartedEvent()
        assert event.request_id == ""
        assert event.provider == ""
        assert event.model_id == ""

    def test_has_event_metadata(self) -> None:
        """Verify DomainEvent metadata is present."""
        event = InferenceStartedEvent(request_id="r1", provider="p1", model_id="m1")
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_is_frozen(self) -> None:
        """Verify event is immutable."""
        event = InferenceStartedEvent(request_id="r1", provider="p1", model_id="m1")
        with pytest.raises((TypeError, AttributeError)):
            event.request_id = "changed"  # type: ignore[misc]


class TestInferenceCompletedEvent:
    """Tests for InferenceCompletedEvent."""

    def test_is_domain_event(self) -> None:
        """Verify event inherits from DomainEvent."""
        event = InferenceCompletedEvent()
        assert isinstance(event, DomainEvent)

    def test_all_fields(self) -> None:
        """Verify all metrics fields."""
        event = InferenceCompletedEvent(
            request_id="req-1",
            provider="ollama",
            model_id="llama3.2",
            tokens_input=100,
            tokens_output=50,
            latency_ms=250.5,
        )
        assert event.request_id == "req-1"
        assert event.tokens_input == 100
        assert event.tokens_output == 50
        assert event.latency_ms == 250.5

    def test_default_metric_values(self) -> None:
        """Verify default values for metrics are zero."""
        event = InferenceCompletedEvent()
        assert event.tokens_input == 0
        assert event.tokens_output == 0
        assert event.latency_ms == 0.0


class TestInferenceFailedEvent:
    """Tests for InferenceFailedEvent."""

    def test_carries_error_message(self) -> None:
        """Verify error field is stored correctly."""
        event = InferenceFailedEvent(
            request_id="req-fail",
            provider="openai",
            model_id="gpt-4o",
            error="Connection refused",
        )
        assert event.error == "Connection refused"
        assert event.provider == "openai"

    def test_is_domain_event(self) -> None:
        """Verify inheritance."""
        event = InferenceFailedEvent()
        assert isinstance(event, DomainEvent)

    def test_default_error_empty(self) -> None:
        """Verify default error is empty string."""
        event = InferenceFailedEvent()
        assert event.error == ""


class TestProviderHealthChangedEvent:
    """Tests for ProviderHealthChangedEvent."""

    def test_healthy_state(self) -> None:
        """Test event with healthy state."""
        event = ProviderHealthChangedEvent(provider="ollama", healthy=True)
        assert event.provider == "ollama"
        assert event.healthy is True

    def test_unhealthy_state(self) -> None:
        """Test event with unhealthy state."""
        event = ProviderHealthChangedEvent(provider="openai", healthy=False)
        assert event.provider == "openai"
        assert event.healthy is False

    def test_is_domain_event(self) -> None:
        """Verify inheritance."""
        event = ProviderHealthChangedEvent()
        assert isinstance(event, DomainEvent)

    def test_default_healthy(self) -> None:
        """Default healthy should be True."""
        event = ProviderHealthChangedEvent()
        assert event.healthy is True
