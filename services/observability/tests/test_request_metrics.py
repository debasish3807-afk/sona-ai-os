"""Unit tests for the RequestMetrics infrastructure module.

Tests cover HTTP request metric recording including counters,
histograms, and active request gauges.
"""

from sona_observability.infrastructure.metrics_registry import MetricsRegistry
from sona_observability.infrastructure.request_metrics import RequestMetrics


class TestRequestMetricRecording:
    """Tests for recording HTTP request metrics."""

    def test_record_increments_total(self) -> None:
        """Recording a request increments the total counter."""
        registry = MetricsRegistry()
        rm = RequestMetrics(registry)
        rm.record_request("GET", "/api/health", 200, 50.0)
        assert (
            registry.get_counter(
                "http_requests_total",
                tags={"method": "GET", "path": "/api/health", "status": "200"},
            )
            == 1.0
        )

    def test_record_multiple_requests(self) -> None:
        """Multiple requests accumulate correctly."""
        registry = MetricsRegistry()
        rm = RequestMetrics(registry)
        rm.record_request("GET", "/api", 200, 10.0)
        rm.record_request("GET", "/api", 200, 20.0)
        rm.record_request("POST", "/api", 201, 30.0)
        assert (
            registry.get_counter(
                "http_requests_total",
                tags={"method": "GET", "path": "/api", "status": "200"},
            )
            == 2.0
        )
        assert (
            registry.get_counter(
                "http_requests_total",
                tags={"method": "POST", "path": "/api", "status": "201"},
            )
            == 1.0
        )

    def test_record_duration_histogram(self) -> None:
        """Recording a request records duration in histogram."""
        registry = MetricsRegistry()
        rm = RequestMetrics(registry)
        rm.record_request("GET", "/api", 200, 150.5)
        values = registry.get_histogram_values(
            "http_request_duration_ms",
            tags={"method": "GET", "path": "/api"},
        )
        assert values == [150.5]

    def test_record_error_status(self) -> None:
        """Error status codes are recorded correctly."""
        registry = MetricsRegistry()
        rm = RequestMetrics(registry)
        rm.record_request("GET", "/api", 500, 100.0)
        assert (
            registry.get_counter(
                "http_requests_total",
                tags={"method": "GET", "path": "/api", "status": "500"},
            )
            == 1.0
        )


class TestActiveRequests:
    """Tests for active request tracking."""

    def test_increment_active(self) -> None:
        """Incrementing active requests increases gauge."""
        registry = MetricsRegistry()
        rm = RequestMetrics(registry)
        rm.increment_active()
        assert registry.get_gauge("http_requests_active") == 1.0

    def test_decrement_active(self) -> None:
        """Decrementing active requests decreases gauge."""
        registry = MetricsRegistry()
        rm = RequestMetrics(registry)
        rm.increment_active()
        rm.increment_active()
        rm.decrement_active()
        assert registry.get_gauge("http_requests_active") == 1.0

    def test_decrement_does_not_go_negative(self) -> None:
        """Active requests gauge doesn't go below zero."""
        registry = MetricsRegistry()
        rm = RequestMetrics(registry)
        rm.decrement_active()
        assert registry.get_gauge("http_requests_active") == 0.0

    def test_multiple_increment_decrement(self) -> None:
        """Multiple increment/decrement cycles work correctly."""
        registry = MetricsRegistry()
        rm = RequestMetrics(registry)
        rm.increment_active()
        rm.increment_active()
        rm.increment_active()
        rm.decrement_active()
        assert registry.get_gauge("http_requests_active") == 2.0
