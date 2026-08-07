"""Unit tests for Observability domain events.

Tests verify that all domain events are correctly defined, instantiate
properly, inherit from DomainEvent, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_observability.domain.events import (
    AlertTriggeredEvent,
    MetricRecordedEvent,
    SpanEndedEvent,
    SpanStartedEvent,
)
from sona_shared.domain.primitives import DomainEvent


class TestMetricRecordedEvent:
    """Tests for MetricRecordedEvent."""

    def test_inherits_domain_event(self) -> None:
        """Verify it inherits from DomainEvent."""
        event = MetricRecordedEvent()
        assert isinstance(event, DomainEvent)

    def test_default_values(self) -> None:
        """Verify default field values."""
        event = MetricRecordedEvent()
        assert event.name == ""
        assert event.metric_type == ""
        assert event.value == 0.0

    def test_custom_values(self) -> None:
        """Verify custom field values."""
        event = MetricRecordedEvent(
            name="http_requests_total",
            metric_type="counter",
            value=42.0,
        )
        assert event.name == "http_requests_total"
        assert event.metric_type == "counter"
        assert event.value == 42.0

    def test_is_frozen(self) -> None:
        """Verify event is immutable."""
        event = MetricRecordedEvent(name="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.name = "changed"  # type: ignore[misc]

    def test_has_event_id(self) -> None:
        """Verify DomainEvent fields are present."""
        event = MetricRecordedEvent()
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_equality(self) -> None:
        """Verify two events with same event_id are equal."""
        event1 = MetricRecordedEvent(name="test", value=1.0)
        event2 = MetricRecordedEvent(name="test", value=1.0)
        # Different event_ids means not equal
        assert event1 != event2

    def test_hashable(self) -> None:
        """Verify event is hashable."""
        event = MetricRecordedEvent(name="test")
        event_set = {event}
        assert event in event_set


class TestSpanStartedEvent:
    """Tests for SpanStartedEvent."""

    def test_inherits_domain_event(self) -> None:
        """Verify it inherits from DomainEvent."""
        event = SpanStartedEvent()
        assert isinstance(event, DomainEvent)

    def test_default_values(self) -> None:
        """Verify default field values."""
        event = SpanStartedEvent()
        assert event.trace_id == ""
        assert event.span_id == ""
        assert event.operation == ""

    def test_custom_values(self) -> None:
        """Verify custom field values."""
        event = SpanStartedEvent(
            trace_id="trace-123",
            span_id="span-456",
            operation="process_request",
        )
        assert event.trace_id == "trace-123"
        assert event.span_id == "span-456"
        assert event.operation == "process_request"

    def test_is_frozen(self) -> None:
        """Verify event is immutable."""
        event = SpanStartedEvent(trace_id="t1")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.trace_id = "changed"  # type: ignore[misc]

    def test_has_event_id(self) -> None:
        """Verify DomainEvent fields are present."""
        event = SpanStartedEvent()
        assert event.event_id is not None

    def test_hashable(self) -> None:
        """Verify event is hashable."""
        event = SpanStartedEvent(trace_id="t1", span_id="s1")
        event_set = {event}
        assert event in event_set


class TestSpanEndedEvent:
    """Tests for SpanEndedEvent."""

    def test_inherits_domain_event(self) -> None:
        """Verify it inherits from DomainEvent."""
        event = SpanEndedEvent()
        assert isinstance(event, DomainEvent)

    def test_default_values(self) -> None:
        """Verify default field values."""
        event = SpanEndedEvent()
        assert event.trace_id == ""
        assert event.span_id == ""
        assert event.duration_ms == 0.0
        assert event.status == "ok"

    def test_custom_values(self) -> None:
        """Verify custom field values."""
        event = SpanEndedEvent(
            trace_id="trace-abc",
            span_id="span-def",
            duration_ms=150.5,
            status="error",
        )
        assert event.trace_id == "trace-abc"
        assert event.span_id == "span-def"
        assert event.duration_ms == 150.5
        assert event.status == "error"

    def test_is_frozen(self) -> None:
        """Verify event is immutable."""
        event = SpanEndedEvent(status="ok")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.status = "error"  # type: ignore[misc]

    def test_has_event_id(self) -> None:
        """Verify DomainEvent fields are present."""
        event = SpanEndedEvent()
        assert event.event_id is not None

    def test_default_status_is_ok(self) -> None:
        """Verify default status is 'ok'."""
        event = SpanEndedEvent()
        assert event.status == "ok"

    def test_hashable(self) -> None:
        """Verify event is hashable."""
        event = SpanEndedEvent(trace_id="t1", span_id="s1")
        event_set = {event}
        assert event in event_set


class TestAlertTriggeredEvent:
    """Tests for AlertTriggeredEvent."""

    def test_inherits_domain_event(self) -> None:
        """Verify it inherits from DomainEvent."""
        event = AlertTriggeredEvent()
        assert isinstance(event, DomainEvent)

    def test_default_values(self) -> None:
        """Verify default field values."""
        event = AlertTriggeredEvent()
        assert event.metric_name == ""
        assert event.threshold == 0.0
        assert event.current_value == 0.0

    def test_custom_values(self) -> None:
        """Verify custom field values."""
        event = AlertTriggeredEvent(
            metric_name="error_rate",
            threshold=0.05,
            current_value=0.08,
        )
        assert event.metric_name == "error_rate"
        assert event.threshold == 0.05
        assert event.current_value == 0.08

    def test_is_frozen(self) -> None:
        """Verify event is immutable."""
        event = AlertTriggeredEvent(metric_name="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            event.metric_name = "changed"  # type: ignore[misc]

    def test_has_event_id(self) -> None:
        """Verify DomainEvent fields are present."""
        event = AlertTriggeredEvent()
        assert event.event_id is not None

    def test_threshold_exceeded(self) -> None:
        """Verify alert represents threshold exceeded condition."""
        event = AlertTriggeredEvent(
            metric_name="latency_p99",
            threshold=500.0,
            current_value=750.0,
        )
        assert event.current_value > event.threshold

    def test_hashable(self) -> None:
        """Verify event is hashable."""
        event = AlertTriggeredEvent(metric_name="test")
        event_set = {event}
        assert event in event_set
