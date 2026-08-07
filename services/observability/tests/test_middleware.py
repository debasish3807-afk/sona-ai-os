"""Unit tests for the ObservabilityMiddleware infrastructure module.

Tests cover span creation, metric recording, correlation propagation,
and request lifecycle instrumentation.
"""

from sona_observability.infrastructure.metrics_registry import MetricsRegistry
from sona_observability.infrastructure.middleware import ObservabilityMiddleware
from sona_observability.infrastructure.structured_logger import StructuredLogger
from sona_observability.infrastructure.tracer import Tracer


class TestMiddlewareSpanCreation:
    """Tests for middleware span creation."""

    def test_before_request_creates_span(self) -> None:
        """before_request creates an active span."""
        tracer = Tracer(service_name="test-svc")
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api/health")
        assert ctx.span_id != ""
        assert ctx.trace_id != ""

    def test_after_request_ends_span(self) -> None:
        """after_request ends the span created by before_request."""
        tracer = Tracer(service_name="test-svc")
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        mw.after_request(ctx, 200)
        # Span should be completed
        assert len(tracer.completed_spans) == 1

    def test_span_has_correct_operation(self) -> None:
        """Span operation includes method and path."""
        tracer = Tracer(service_name="test-svc")
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("POST", "/v1/chat")
        mw.after_request(ctx, 200)
        completed = tracer.completed_spans[0]
        assert "POST" in completed.context.operation
        assert "/v1/chat" in completed.context.operation


class TestMiddlewareMetrics:
    """Tests for middleware metric recording."""

    def test_records_request_count(self) -> None:
        """Middleware records request in http_requests_total."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        mw.after_request(ctx, 200)
        assert (
            registry.get_counter(
                "http_requests_total",
                tags={"method": "GET", "path": "/api", "status": "200"},
            )
            == 1.0
        )

    def test_records_request_duration(self) -> None:
        """Middleware records request duration."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("POST", "/v1/chat")
        mw.after_request(ctx, 201)
        values = registry.get_histogram_values(
            "http_request_duration_ms",
            tags={"method": "POST", "path": "/v1/chat"},
        )
        assert len(values) == 1
        assert values[0] >= 0

    def test_tracks_active_requests(self) -> None:
        """Middleware increments/decrements active requests."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        # Active should be 1
        assert registry.get_gauge("http_requests_active") == 1.0
        mw.after_request(ctx, 200)
        # Active should be 0
        assert registry.get_gauge("http_requests_active") == 0.0

    def test_error_status_records_correctly(self) -> None:
        """5xx status codes recorded with correct status."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        mw.after_request(ctx, 500, error="Internal error")
        assert (
            registry.get_counter(
                "http_requests_total",
                tags={"method": "GET", "path": "/api", "status": "500"},
            )
            == 1.0
        )


class TestMiddlewareCorrelation:
    """Tests for correlation ID propagation."""

    def test_generates_request_id(self) -> None:
        """Middleware generates a request_id."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        assert ctx.request_id != ""

    def test_generates_trace_id(self) -> None:
        """Middleware generates a trace_id."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        assert ctx.trace_id != ""

    def test_propagates_existing_request_id(self) -> None:
        """Middleware uses existing request_id from headers."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api", headers={"x-request-id": "existing-req-id"})
        assert ctx.request_id == "existing-req-id"

    def test_response_headers_include_correlation(self) -> None:
        """after_request returns correlation headers."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        response_headers = mw.after_request(ctx, 200)
        assert "x-request-id" in response_headers


class TestMiddlewareLogging:
    """Tests for middleware logging."""

    def test_logs_request_start(self) -> None:
        """Middleware logs request start."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        mw.before_request("GET", "/api/health")
        assert len(logger.entries) >= 1
        assert "started" in logger.entries[0]["message"].lower()

    def test_logs_request_completion(self) -> None:
        """Middleware logs request completion."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        mw.after_request(ctx, 200)
        # Should have at least 2 log entries (start + end)
        assert len(logger.entries) >= 2
        last_entry = logger.entries[-1]
        assert "completed" in last_entry["message"].lower()

    def test_logs_include_request_context(self) -> None:
        """Log entries include request context (method, path)."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("POST", "/v1/chat")
        mw.after_request(ctx, 200)
        last_entry = logger.entries[-1]
        assert last_entry.get("method") == "POST"
        assert last_entry.get("path") == "/v1/chat"

    def test_error_response_logs_at_error_level(self) -> None:
        """5xx responses are logged at ERROR level."""
        tracer = Tracer()
        registry = MetricsRegistry()
        logger = StructuredLogger()
        mw = ObservabilityMiddleware(tracer, registry, logger)

        ctx = mw.before_request("GET", "/api")
        mw.after_request(ctx, 503)
        last_entry = logger.entries[-1]
        assert last_entry["level"] == "error"
