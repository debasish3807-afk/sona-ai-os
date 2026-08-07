"""Unit tests for the Tracer infrastructure module.

Tests cover span creation, parent-child relationships, UUID-based IDs,
duration computation, context injection/extraction, and span attributes.
"""

import time

from sona_observability.application.ports import TracingPort
from sona_observability.domain.models import SpanContext
from sona_observability.infrastructure.tracer import Tracer


class TestTracerInterface:
    """Verify Tracer implements TracingPort."""

    def test_implements_tracing_port(self) -> None:
        """Tracer should implement TracingPort."""
        tracer = Tracer()
        assert isinstance(tracer, TracingPort)


class TestSpanCreation:
    """Tests for starting spans."""

    def test_start_span_returns_span_context(self) -> None:
        """start_span returns a SpanContext."""
        tracer = Tracer()
        span = tracer.start_span("test_operation")
        assert isinstance(span, SpanContext)

    def test_span_has_trace_id(self) -> None:
        """Span has a non-empty trace_id."""
        tracer = Tracer()
        span = tracer.start_span("test")
        assert span.trace_id != ""
        assert len(span.trace_id) == 32  # UUID hex

    def test_span_has_span_id(self) -> None:
        """Span has a non-empty span_id."""
        tracer = Tracer()
        span = tracer.start_span("test")
        assert span.span_id != ""
        assert len(span.span_id) == 32  # UUID hex

    def test_span_has_operation(self) -> None:
        """Span records the operation name."""
        tracer = Tracer()
        span = tracer.start_span("process_request")
        assert span.operation == "process_request"

    def test_span_has_service_name(self) -> None:
        """Span records the service name."""
        tracer = Tracer(service_name="my-service")
        span = tracer.start_span("test")
        assert span.service_name == "my-service"

    def test_root_span_has_no_parent(self) -> None:
        """Root span has no parent_span_id."""
        tracer = Tracer()
        span = tracer.start_span("root_op")
        assert span.parent_span_id is None

    def test_each_span_gets_unique_ids(self) -> None:
        """Each span gets unique trace_id and span_id."""
        tracer = Tracer()
        span1 = tracer.start_span("op1")
        span2 = tracer.start_span("op2")
        assert span1.trace_id != span2.trace_id
        assert span1.span_id != span2.span_id

    def test_span_tracked_as_active(self) -> None:
        """Started span is tracked in active spans."""
        tracer = Tracer()
        span = tracer.start_span("test")
        assert span.span_id in tracer.active_spans


class TestParentChildSpans:
    """Tests for parent-child span relationships."""

    def test_child_span_inherits_trace_id(self) -> None:
        """Child span inherits parent's trace_id."""
        tracer = Tracer()
        parent = tracer.start_span("parent_op")
        child = tracer.start_span("child_op", parent=parent)
        assert child.trace_id == parent.trace_id

    def test_child_span_references_parent(self) -> None:
        """Child span has parent's span_id as parent_span_id."""
        tracer = Tracer()
        parent = tracer.start_span("parent_op")
        child = tracer.start_span("child_op", parent=parent)
        assert child.parent_span_id == parent.span_id

    def test_child_has_unique_span_id(self) -> None:
        """Child span has its own unique span_id."""
        tracer = Tracer()
        parent = tracer.start_span("parent")
        child = tracer.start_span("child", parent=parent)
        assert child.span_id != parent.span_id

    def test_grandchild_span(self) -> None:
        """Grandchild span references child as parent."""
        tracer = Tracer()
        root = tracer.start_span("root")
        child = tracer.start_span("child", parent=root)
        grandchild = tracer.start_span("grandchild", parent=child)
        assert grandchild.trace_id == root.trace_id
        assert grandchild.parent_span_id == child.span_id

    def test_multiple_children(self) -> None:
        """Parent can have multiple child spans."""
        tracer = Tracer()
        parent = tracer.start_span("parent")
        child1 = tracer.start_span("child1", parent=parent)
        child2 = tracer.start_span("child2", parent=parent)
        assert child1.parent_span_id == parent.span_id
        assert child2.parent_span_id == parent.span_id
        assert child1.span_id != child2.span_id


class TestEndSpan:
    """Tests for ending spans."""

    def test_end_span_removes_from_active(self) -> None:
        """Ending a span removes it from active spans."""
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.end_span(span)
        assert span.span_id not in tracer.active_spans

    def test_end_span_adds_to_completed(self) -> None:
        """Ending a span adds it to completed spans."""
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.end_span(span)
        assert len(tracer.completed_spans) == 1

    def test_end_span_default_status(self) -> None:
        """Default end status is 'ok'."""
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.end_span(span)
        assert tracer.completed_spans[0].status == "ok"

    def test_end_span_error_status(self) -> None:
        """Can end span with error status."""
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.end_span(span, status="error")
        assert tracer.completed_spans[0].status == "error"

    def test_end_nonexistent_span(self) -> None:
        """Ending a nonexistent span is a no-op."""
        tracer = Tracer()
        fake_span = SpanContext(trace_id="fake", span_id="fake")
        tracer.end_span(fake_span)  # Should not raise
        assert len(tracer.completed_spans) == 0


class TestSpanDuration:
    """Tests for span duration computation."""

    def test_duration_is_positive(self) -> None:
        """Completed span has positive duration."""
        tracer = Tracer()
        span = tracer.start_span("test")
        time.sleep(0.01)  # 10ms
        tracer.end_span(span)
        duration = tracer.get_span_duration(span)
        assert duration is not None
        assert duration > 0

    def test_duration_approximately_correct(self) -> None:
        """Span duration is approximately the elapsed time."""
        tracer = Tracer()
        span = tracer.start_span("test")
        time.sleep(0.05)  # 50ms
        tracer.end_span(span)
        duration = tracer.get_span_duration(span)
        assert duration is not None
        assert 40.0 <= duration <= 150.0  # Allow tolerance

    def test_duration_unknown_span(self) -> None:
        """Getting duration of unknown span returns None."""
        tracer = Tracer()
        fake_span = SpanContext(trace_id="fake", span_id="fake")
        assert tracer.get_span_duration(fake_span) is None


class TestContextInjection:
    """Tests for context injection into headers."""

    def test_inject_produces_traceparent(self) -> None:
        """inject_context produces a traceparent header."""
        tracer = Tracer()
        span = tracer.start_span("test")
        headers = tracer.inject_context(span)
        assert "traceparent" in headers

    def test_traceparent_format(self) -> None:
        """traceparent follows W3C format: version-traceid-spanid-flags."""
        tracer = Tracer()
        span = tracer.start_span("test")
        headers = tracer.inject_context(span)
        parts = headers["traceparent"].split("-")
        assert len(parts) == 4
        assert parts[0] == "00"
        assert parts[1] == span.trace_id
        assert parts[2] == span.span_id
        assert parts[3] == "01"

    def test_inject_includes_tracestate(self) -> None:
        """inject_context includes tracestate with service name."""
        tracer = Tracer(service_name="my-service")
        span = tracer.start_span("test")
        headers = tracer.inject_context(span)
        assert "tracestate" in headers
        assert "my-service" in headers["tracestate"]


class TestContextExtraction:
    """Tests for context extraction from headers."""

    def test_extract_valid_traceparent(self) -> None:
        """Extract context from valid traceparent header."""
        tracer = Tracer()
        headers = {"traceparent": "00-abc123def456-span789-01"}
        ctx = tracer.extract_context(headers)
        assert ctx is not None
        assert ctx.trace_id == "abc123def456"
        assert ctx.span_id == "span789"

    def test_extract_with_tracestate(self) -> None:
        """Extract context including tracestate service name."""
        tracer = Tracer()
        headers = {
            "traceparent": "00-trace123-span456-01",
            "tracestate": "service=upstream-svc",
        }
        ctx = tracer.extract_context(headers)
        assert ctx is not None
        assert ctx.service_name == "upstream-svc"

    def test_extract_missing_traceparent(self) -> None:
        """Missing traceparent returns None."""
        tracer = Tracer()
        ctx = tracer.extract_context({})
        assert ctx is None

    def test_extract_invalid_traceparent(self) -> None:
        """Invalid traceparent format returns None."""
        tracer = Tracer()
        ctx = tracer.extract_context({"traceparent": "invalid"})
        assert ctx is None

    def test_roundtrip_inject_extract(self) -> None:
        """Injected context can be extracted back."""
        tracer = Tracer(service_name="test-svc")
        span = tracer.start_span("op")
        headers = tracer.inject_context(span)
        extracted = tracer.extract_context(headers)
        assert extracted is not None
        assert extracted.trace_id == span.trace_id
        assert extracted.span_id == span.span_id


class TestSpanAttributes:
    """Tests for span attributes."""

    def test_set_attribute(self) -> None:
        """Can set attributes on active span."""
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.set_attribute(span, "http.method", "GET")
        record = tracer.active_spans[span.span_id]
        assert record.attributes["http.method"] == "GET"

    def test_set_multiple_attributes(self) -> None:
        """Can set multiple attributes."""
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.set_attribute(span, "http.method", "POST")
        tracer.set_attribute(span, "http.status", 200)
        record = tracer.active_spans[span.span_id]
        assert record.attributes == {"http.method": "POST", "http.status": 200}

    def test_set_attribute_on_ended_span(self) -> None:
        """Setting attribute on ended span is a no-op."""
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.end_span(span)
        tracer.set_attribute(span, "key", "value")  # Should not raise


class TestServiceName:
    """Tests for service name configuration."""

    def test_default_service_name(self) -> None:
        """Default service name is 'sona-ai-os'."""
        tracer = Tracer()
        assert tracer.service_name == "sona-ai-os"

    def test_custom_service_name(self) -> None:
        """Custom service name is used."""
        tracer = Tracer(service_name="ai-kernel")
        assert tracer.service_name == "ai-kernel"
        span = tracer.start_span("test")
        assert span.service_name == "ai-kernel"
