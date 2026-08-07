"""Unit tests for Observability abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest
from sona_observability.application.ports import LoggingPort, MetricsPort, TracingPort
from sona_observability.domain.models import LogLevel, SpanContext


class TestMetricsPort:
    """Tests for the MetricsPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify MetricsPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MetricsPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = MetricsPort.__abstractmethods__
        assert "increment" in abstract_methods
        assert "gauge" in abstract_methods
        assert "histogram" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteMetrics(MetricsPort):
            def __init__(self) -> None:
                self.recorded: list[tuple[str, str, float, dict | None]] = []

            def increment(self, name: str, value: float = 1.0, tags: dict | None = None) -> None:
                self.recorded.append(("increment", name, value, tags))

            def gauge(self, name: str, value: float, tags: dict | None = None) -> None:
                self.recorded.append(("gauge", name, value, tags))

            def histogram(self, name: str, value: float, tags: dict | None = None) -> None:
                self.recorded.append(("histogram", name, value, tags))

        metrics = ConcreteMetrics()
        assert isinstance(metrics, MetricsPort)

    def test_increment_with_default_value(self) -> None:
        """Test that increment works with default value of 1.0."""

        class MockMetrics(MetricsPort):
            def __init__(self) -> None:
                self.last_increment: tuple[str, float, dict | None] | None = None

            def increment(self, name: str, value: float = 1.0, tags: dict | None = None) -> None:
                self.last_increment = (name, value, tags)

            def gauge(self, name: str, value: float, tags: dict | None = None) -> None:
                pass

            def histogram(self, name: str, value: float, tags: dict | None = None) -> None:
                pass

        metrics = MockMetrics()
        metrics.increment("requests_total")
        assert metrics.last_increment == ("requests_total", 1.0, None)

    def test_increment_with_custom_value_and_tags(self) -> None:
        """Test that increment works with custom value and tags."""

        class MockMetrics(MetricsPort):
            def __init__(self) -> None:
                self.last_increment: tuple[str, float, dict | None] | None = None

            def increment(self, name: str, value: float = 1.0, tags: dict | None = None) -> None:
                self.last_increment = (name, value, tags)

            def gauge(self, name: str, value: float, tags: dict | None = None) -> None:
                pass

            def histogram(self, name: str, value: float, tags: dict | None = None) -> None:
                pass

        metrics = MockMetrics()
        metrics.increment("errors_total", 5.0, {"service": "ai-kernel"})
        assert metrics.last_increment == ("errors_total", 5.0, {"service": "ai-kernel"})

    def test_gauge_records_value(self) -> None:
        """Test that gauge records the current value."""

        class MockMetrics(MetricsPort):
            def __init__(self) -> None:
                self.last_gauge: tuple[str, float, dict | None] | None = None

            def increment(self, name: str, value: float = 1.0, tags: dict | None = None) -> None:
                pass

            def gauge(self, name: str, value: float, tags: dict | None = None) -> None:
                self.last_gauge = (name, value, tags)

            def histogram(self, name: str, value: float, tags: dict | None = None) -> None:
                pass

        metrics = MockMetrics()
        metrics.gauge("active_connections", 42.0, {"host": "node-1"})
        assert metrics.last_gauge == ("active_connections", 42.0, {"host": "node-1"})

    def test_histogram_records_observation(self) -> None:
        """Test that histogram records an observed value."""

        class MockMetrics(MetricsPort):
            def __init__(self) -> None:
                self.last_histogram: tuple[str, float, dict | None] | None = None

            def increment(self, name: str, value: float = 1.0, tags: dict | None = None) -> None:
                pass

            def gauge(self, name: str, value: float, tags: dict | None = None) -> None:
                pass

            def histogram(self, name: str, value: float, tags: dict | None = None) -> None:
                self.last_histogram = (name, value, tags)

        metrics = MockMetrics()
        metrics.histogram("request_duration_ms", 150.5)
        assert metrics.last_histogram == ("request_duration_ms", 150.5, None)


class TestTracingPort:
    """Tests for the TracingPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify TracingPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TracingPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = TracingPort.__abstractmethods__
        assert "start_span" in abstract_methods
        assert "end_span" in abstract_methods
        assert "inject_context" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteTracing(TracingPort):
            def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
                return SpanContext(
                    trace_id="trace-1",
                    span_id="span-new",
                    parent_span_id=parent.span_id if parent else None,
                    service_name="test-service",
                    operation=operation,
                )

            def end_span(self, span: SpanContext, status: str = "ok") -> None:
                pass

            def inject_context(self, span: SpanContext) -> dict[str, str]:
                return {
                    "traceparent": f"00-{span.trace_id}-{span.span_id}-01",
                }

        tracing = ConcreteTracing()
        assert isinstance(tracing, TracingPort)

    def test_start_span_returns_span_context(self) -> None:
        """Test that start_span returns a properly formed SpanContext."""

        class MockTracing(TracingPort):
            def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
                return SpanContext(
                    trace_id="trace-abc",
                    span_id="span-123",
                    parent_span_id=parent.span_id if parent else None,
                    service_name="gateway",
                    operation=operation,
                )

            def end_span(self, span: SpanContext, status: str = "ok") -> None:
                pass

            def inject_context(self, span: SpanContext) -> dict[str, str]:
                return {}

        tracing = MockTracing()
        span = tracing.start_span("handle_request")
        assert isinstance(span, SpanContext)
        assert span.operation == "handle_request"
        assert span.parent_span_id is None

    def test_start_child_span(self) -> None:
        """Test creating a child span with a parent reference."""

        class MockTracing(TracingPort):
            def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
                return SpanContext(
                    trace_id=parent.trace_id if parent else "trace-new",
                    span_id="span-child",
                    parent_span_id=parent.span_id if parent else None,
                    service_name="ai-kernel",
                    operation=operation,
                )

            def end_span(self, span: SpanContext, status: str = "ok") -> None:
                pass

            def inject_context(self, span: SpanContext) -> dict[str, str]:
                return {}

        tracing = MockTracing()
        parent = SpanContext(trace_id="trace-1", span_id="span-parent")
        child = tracing.start_span("process", parent=parent)
        assert child.parent_span_id == "span-parent"
        assert child.trace_id == "trace-1"

    def test_end_span_with_default_status(self) -> None:
        """Test ending a span with default 'ok' status."""

        class MockTracing(TracingPort):
            def __init__(self) -> None:
                self.ended_spans: list[tuple[SpanContext, str]] = []

            def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
                return SpanContext(trace_id="t1", span_id="s1", operation=operation)

            def end_span(self, span: SpanContext, status: str = "ok") -> None:
                self.ended_spans.append((span, status))

            def inject_context(self, span: SpanContext) -> dict[str, str]:
                return {}

        tracing = MockTracing()
        span = SpanContext(trace_id="t1", span_id="s1", operation="test")
        tracing.end_span(span)
        assert tracing.ended_spans == [(span, "ok")]

    def test_end_span_with_error_status(self) -> None:
        """Test ending a span with error status."""

        class MockTracing(TracingPort):
            def __init__(self) -> None:
                self.ended_spans: list[tuple[SpanContext, str]] = []

            def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
                return SpanContext(trace_id="t1", span_id="s1", operation=operation)

            def end_span(self, span: SpanContext, status: str = "ok") -> None:
                self.ended_spans.append((span, status))

            def inject_context(self, span: SpanContext) -> dict[str, str]:
                return {}

        tracing = MockTracing()
        span = SpanContext(trace_id="t1", span_id="s1", operation="failed_op")
        tracing.end_span(span, status="error")
        assert tracing.ended_spans == [(span, "error")]

    def test_inject_context_returns_headers(self) -> None:
        """Test that inject_context returns propagation headers."""

        class MockTracing(TracingPort):
            def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
                return SpanContext(trace_id="t1", span_id="s1", operation=operation)

            def end_span(self, span: SpanContext, status: str = "ok") -> None:
                pass

            def inject_context(self, span: SpanContext) -> dict[str, str]:
                return {
                    "traceparent": f"00-{span.trace_id}-{span.span_id}-01",
                    "tracestate": f"service={span.service_name}",
                }

        tracing = MockTracing()
        span = SpanContext(trace_id="abc123", span_id="def456", service_name="gateway")
        headers = tracing.inject_context(span)
        assert "traceparent" in headers
        assert "abc123" in headers["traceparent"]
        assert "def456" in headers["traceparent"]


class TestLoggingPort:
    """Tests for the LoggingPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify LoggingPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LoggingPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = LoggingPort.__abstractmethods__
        assert "log" in abstract_methods
        assert "with_context" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteLogger(LoggingPort):
            def __init__(self, context: dict | None = None) -> None:
                self._context = context or {}

            def log(self, level: LogLevel, message: str, context: dict | None = None) -> None:
                pass

            def with_context(self, **kwargs) -> "LoggingPort":
                new_context = {**self._context, **kwargs}
                return ConcreteLogger(context=new_context)

        logger = ConcreteLogger()
        assert isinstance(logger, LoggingPort)

    def test_log_with_all_levels(self) -> None:
        """Test that log accepts all LogLevel values."""

        class MockLogger(LoggingPort):
            def __init__(self) -> None:
                self.entries: list[tuple[LogLevel, str, dict | None]] = []

            def log(self, level: LogLevel, message: str, context: dict | None = None) -> None:
                self.entries.append((level, message, context))

            def with_context(self, **kwargs) -> "LoggingPort":
                return self

        logger = MockLogger()
        for level in LogLevel:
            logger.log(level, f"Test message at {level}")

        assert len(logger.entries) == 5
        assert logger.entries[0][0] == LogLevel.DEBUG
        assert logger.entries[-1][0] == LogLevel.CRITICAL

    def test_log_with_context(self) -> None:
        """Test logging with structured context data."""

        class MockLogger(LoggingPort):
            def __init__(self) -> None:
                self.last_entry: tuple[LogLevel, str, dict | None] | None = None

            def log(self, level: LogLevel, message: str, context: dict | None = None) -> None:
                self.last_entry = (level, message, context)

            def with_context(self, **kwargs) -> "LoggingPort":
                return self

        logger = MockLogger()
        logger.log(
            LogLevel.ERROR,
            "Request failed",
            {"request_id": "req-123", "status_code": 500},
        )
        assert logger.last_entry is not None
        assert logger.last_entry[0] == LogLevel.ERROR
        assert logger.last_entry[1] == "Request failed"
        assert logger.last_entry[2] == {"request_id": "req-123", "status_code": 500}

    def test_with_context_returns_logging_port(self) -> None:
        """Test that with_context returns a LoggingPort instance."""

        class MockLogger(LoggingPort):
            def __init__(self, bound_context: dict | None = None) -> None:
                self._bound = bound_context or {}

            def log(self, level: LogLevel, message: str, context: dict | None = None) -> None:
                pass

            def with_context(self, **kwargs) -> "LoggingPort":
                new_context = {**self._bound, **kwargs}
                return MockLogger(bound_context=new_context)

        logger = MockLogger()
        scoped_logger = logger.with_context(service="ai-kernel", trace_id="t1")
        assert isinstance(scoped_logger, LoggingPort)

    def test_with_context_preserves_type(self) -> None:
        """Test that with_context preserves bound context across calls."""

        class MockLogger(LoggingPort):
            def __init__(self, bound_context: dict | None = None) -> None:
                self.bound = bound_context or {}
                self.last_entry: tuple[LogLevel, str, dict | None] | None = None

            def log(self, level: LogLevel, message: str, context: dict | None = None) -> None:
                self.last_entry = (level, message, context)

            def with_context(self, **kwargs) -> "MockLogger":
                new_context = {**self.bound, **kwargs}
                return MockLogger(bound_context=new_context)

        logger = MockLogger()
        scoped = logger.with_context(service="gateway", environment="prod")
        assert isinstance(scoped, MockLogger)
        assert scoped.bound == {"service": "gateway", "environment": "prod"}
