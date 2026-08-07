"""Unit tests for Observability domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_observability.domain.models import LogLevel, MetricType, SpanContext


class TestMetricType:
    """Tests for the MetricType enum."""

    def test_all_metric_types_defined(self) -> None:
        """Verify all expected metric types are available."""
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"
        assert MetricType.SUMMARY == "summary"

    def test_metric_type_count(self) -> None:
        """Verify exactly 4 metric types exist."""
        assert len(MetricType) == 4

    def test_metric_type_is_str_enum(self) -> None:
        """Verify metric types are usable as strings."""
        assert str(MetricType.COUNTER) == "counter"
        assert str(MetricType.HISTOGRAM) == "histogram"


class TestLogLevel:
    """Tests for the LogLevel enum."""

    def test_all_log_levels_defined(self) -> None:
        """Verify all expected log levels are available."""
        assert LogLevel.DEBUG == "debug"
        assert LogLevel.INFO == "info"
        assert LogLevel.WARNING == "warning"
        assert LogLevel.ERROR == "error"
        assert LogLevel.CRITICAL == "critical"

    def test_log_level_count(self) -> None:
        """Verify exactly 5 log levels exist."""
        assert len(LogLevel) == 5

    def test_log_level_is_str_enum(self) -> None:
        """Verify log levels are usable as strings."""
        assert str(LogLevel.DEBUG) == "debug"
        assert str(LogLevel.CRITICAL) == "critical"

    def test_log_level_ordering(self) -> None:
        """Verify log levels can be compared as strings for ordering."""
        # StrEnum values are comparable as strings
        levels = list(LogLevel)
        assert levels[0] == LogLevel.DEBUG
        assert levels[-1] == LogLevel.CRITICAL


class TestSpanContext:
    """Tests for the SpanContext frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        span = SpanContext(trace_id="trace-123", span_id="span-456")
        assert span.trace_id == "trace-123"
        assert span.span_id == "span-456"

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        span = SpanContext(trace_id="t1", span_id="s1")
        assert span.parent_span_id is None
        assert span.service_name == ""
        assert span.operation == ""

    def test_full_creation(self) -> None:
        """Create with all fields specified."""
        span = SpanContext(
            trace_id="trace-abc",
            span_id="span-def",
            parent_span_id="span-parent",
            service_name="ai-kernel",
            operation="process_request",
        )
        assert span.trace_id == "trace-abc"
        assert span.span_id == "span-def"
        assert span.parent_span_id == "span-parent"
        assert span.service_name == "ai-kernel"
        assert span.operation == "process_request"

    def test_is_frozen(self) -> None:
        """Verify SpanContext is immutable."""
        span = SpanContext(trace_id="t1", span_id="s1")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            span.trace_id = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Verify two SpanContext with same values are equal."""
        span1 = SpanContext(trace_id="t1", span_id="s1", service_name="svc")
        span2 = SpanContext(trace_id="t1", span_id="s1", service_name="svc")
        assert span1 == span2

    def test_inequality(self) -> None:
        """Verify SpanContext with different values are not equal."""
        span1 = SpanContext(trace_id="t1", span_id="s1")
        span2 = SpanContext(trace_id="t1", span_id="s2")
        assert span1 != span2

    def test_hashable(self) -> None:
        """Verify frozen SpanContext is hashable (usable in sets/dicts)."""
        span = SpanContext(trace_id="t1", span_id="s1")
        span_set = {span}
        assert span in span_set

    def test_root_span_has_no_parent(self) -> None:
        """Verify a root span has parent_span_id as None."""
        root_span = SpanContext(
            trace_id="trace-root",
            span_id="span-root",
            service_name="gateway",
            operation="handle_request",
        )
        assert root_span.parent_span_id is None

    def test_child_span_references_parent(self) -> None:
        """Verify a child span references its parent span ID."""
        parent = SpanContext(
            trace_id="trace-1",
            span_id="span-parent",
            service_name="gateway",
            operation="route",
        )
        child = SpanContext(
            trace_id="trace-1",
            span_id="span-child",
            parent_span_id=parent.span_id,
            service_name="ai-kernel",
            operation="process",
        )
        assert child.parent_span_id == "span-parent"
        assert child.trace_id == parent.trace_id
