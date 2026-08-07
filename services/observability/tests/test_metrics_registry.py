"""Unit tests for the MetricsRegistry infrastructure module.

Tests cover counters, gauges, histograms, percentile computation,
tag-based dimensionality, metric listing, reset, and Prometheus export.
"""

from sona_observability.application.ports import MetricsPort
from sona_observability.domain.models import MetricType
from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class TestMetricsRegistryInterface:
    """Verify MetricsRegistry implements MetricsPort."""

    def test_implements_metrics_port(self) -> None:
        """MetricsRegistry should implement MetricsPort."""
        registry = MetricsRegistry()
        assert isinstance(registry, MetricsPort)


class TestCounters:
    """Tests for counter metric operations."""

    def test_increment_default_value(self) -> None:
        """Counter increments by 1.0 by default."""
        registry = MetricsRegistry()
        registry.increment("requests_total")
        assert registry.get_counter("requests_total") == 1.0

    def test_increment_custom_value(self) -> None:
        """Counter increments by custom value."""
        registry = MetricsRegistry()
        registry.increment("bytes_sent", value=1024.0)
        assert registry.get_counter("bytes_sent") == 1024.0

    def test_increment_accumulates(self) -> None:
        """Multiple increments accumulate."""
        registry = MetricsRegistry()
        registry.increment("requests_total")
        registry.increment("requests_total")
        registry.increment("requests_total", value=3.0)
        assert registry.get_counter("requests_total") == 5.0

    def test_increment_with_tags(self) -> None:
        """Counters with different tags are separate series."""
        registry = MetricsRegistry()
        registry.increment("requests_total", tags={"method": "GET"})
        registry.increment("requests_total", tags={"method": "POST"})
        registry.increment("requests_total", tags={"method": "GET"})
        assert registry.get_counter("requests_total", tags={"method": "GET"}) == 2.0
        assert registry.get_counter("requests_total", tags={"method": "POST"}) == 1.0

    def test_get_nonexistent_counter(self) -> None:
        """Getting a nonexistent counter returns 0.0."""
        registry = MetricsRegistry()
        assert registry.get_counter("nonexistent") == 0.0

    def test_increment_with_multiple_tags(self) -> None:
        """Counter with multiple tags works correctly."""
        registry = MetricsRegistry()
        registry.increment("http_requests", tags={"method": "GET", "path": "/api", "status": "200"})
        assert (
            registry.get_counter(
                "http_requests", tags={"method": "GET", "path": "/api", "status": "200"}
            )
            == 1.0
        )

    def test_tag_order_independent(self) -> None:
        """Tag order shouldn't matter for counter lookup."""
        registry = MetricsRegistry()
        registry.increment("test", tags={"b": "2", "a": "1"})
        assert registry.get_counter("test", tags={"a": "1", "b": "2"}) == 1.0


class TestGauges:
    """Tests for gauge metric operations."""

    def test_gauge_set_value(self) -> None:
        """Gauge sets to specific value."""
        registry = MetricsRegistry()
        registry.gauge("temperature", 36.6)
        assert registry.get_gauge("temperature") == 36.6

    def test_gauge_overwrite(self) -> None:
        """Gauge overwrites previous value."""
        registry = MetricsRegistry()
        registry.gauge("active_connections", 10.0)
        registry.gauge("active_connections", 15.0)
        assert registry.get_gauge("active_connections") == 15.0

    def test_gauge_with_tags(self) -> None:
        """Gauges with different tags are separate series."""
        registry = MetricsRegistry()
        registry.gauge("cpu_usage", 45.0, tags={"host": "node-1"})
        registry.gauge("cpu_usage", 67.0, tags={"host": "node-2"})
        assert registry.get_gauge("cpu_usage", tags={"host": "node-1"}) == 45.0
        assert registry.get_gauge("cpu_usage", tags={"host": "node-2"}) == 67.0

    def test_get_nonexistent_gauge(self) -> None:
        """Getting a nonexistent gauge returns 0.0."""
        registry = MetricsRegistry()
        assert registry.get_gauge("nonexistent") == 0.0

    def test_gauge_negative_value(self) -> None:
        """Gauge can hold negative values."""
        registry = MetricsRegistry()
        registry.gauge("balance", -100.0)
        assert registry.get_gauge("balance") == -100.0

    def test_gauge_zero_value(self) -> None:
        """Gauge can be set to zero."""
        registry = MetricsRegistry()
        registry.gauge("active", 5.0)
        registry.gauge("active", 0.0)
        assert registry.get_gauge("active") == 0.0


class TestHistograms:
    """Tests for histogram metric operations."""

    def test_record_single_value(self) -> None:
        """Histogram records a single value."""
        registry = MetricsRegistry()
        registry.histogram("duration_ms", 150.0)
        assert registry.get_histogram_values("duration_ms") == [150.0]

    def test_record_multiple_values(self) -> None:
        """Histogram records multiple values."""
        registry = MetricsRegistry()
        registry.histogram("duration_ms", 100.0)
        registry.histogram("duration_ms", 200.0)
        registry.histogram("duration_ms", 300.0)
        assert registry.get_histogram_values("duration_ms") == [100.0, 200.0, 300.0]

    def test_histogram_with_tags(self) -> None:
        """Histograms with different tags are separate."""
        registry = MetricsRegistry()
        registry.histogram("latency", 10.0, tags={"endpoint": "/api"})
        registry.histogram("latency", 20.0, tags={"endpoint": "/health"})
        assert registry.get_histogram_values("latency", tags={"endpoint": "/api"}) == [10.0]
        assert registry.get_histogram_values("latency", tags={"endpoint": "/health"}) == [20.0]

    def test_get_nonexistent_histogram(self) -> None:
        """Getting a nonexistent histogram returns empty list."""
        registry = MetricsRegistry()
        assert registry.get_histogram_values("nonexistent") == []


class TestPercentiles:
    """Tests for histogram percentile computation."""

    def test_p50_odd_count(self) -> None:
        """p50 of odd-count values returns median."""
        registry = MetricsRegistry()
        for v in [10, 20, 30, 40, 50]:
            registry.histogram("test", float(v))
        assert registry.percentile("test", 50) == 30.0

    def test_p50_even_count(self) -> None:
        """p50 of even-count values uses interpolation."""
        registry = MetricsRegistry()
        for v in [10, 20, 30, 40]:
            registry.histogram("test", float(v))
        result = registry.percentile("test", 50)
        assert 20.0 <= result <= 30.0

    def test_p95(self) -> None:
        """p95 is computed correctly."""
        registry = MetricsRegistry()
        for v in range(1, 101):
            registry.histogram("latency", float(v))
        p95 = registry.percentile("latency", 95)
        assert 94.0 <= p95 <= 96.0

    def test_p99(self) -> None:
        """p99 is computed correctly."""
        registry = MetricsRegistry()
        for v in range(1, 101):
            registry.histogram("latency", float(v))
        p99 = registry.percentile("latency", 99)
        assert 98.0 <= p99 <= 100.0

    def test_p0_returns_minimum(self) -> None:
        """p0 returns the minimum value."""
        registry = MetricsRegistry()
        for v in [5, 10, 15, 20]:
            registry.histogram("test", float(v))
        assert registry.percentile("test", 0) == 5.0

    def test_p100_returns_maximum(self) -> None:
        """p100 returns the maximum value."""
        registry = MetricsRegistry()
        for v in [5, 10, 15, 20]:
            registry.histogram("test", float(v))
        assert registry.percentile("test", 100) == 20.0

    def test_percentile_single_value(self) -> None:
        """Percentile of single value returns that value."""
        registry = MetricsRegistry()
        registry.histogram("test", 42.0)
        assert registry.percentile("test", 50) == 42.0
        assert registry.percentile("test", 95) == 42.0

    def test_percentile_empty_returns_zero(self) -> None:
        """Percentile of empty histogram returns 0.0."""
        registry = MetricsRegistry()
        assert registry.percentile("test", 50) == 0.0

    def test_percentile_with_tags(self) -> None:
        """Percentile works with tagged histograms."""
        registry = MetricsRegistry()
        for v in [10, 20, 30, 40, 50]:
            registry.histogram("test", float(v), tags={"env": "prod"})
        assert registry.percentile("test", 50, tags={"env": "prod"}) == 30.0


class TestListMetrics:
    """Tests for listing all metrics."""

    def test_list_empty(self) -> None:
        """Listing empty registry returns empty dict."""
        registry = MetricsRegistry()
        assert registry.list_metrics() == {}

    def test_list_counters(self) -> None:
        """Listing includes counters."""
        registry = MetricsRegistry()
        registry.increment("test_counter")
        metrics = registry.list_metrics()
        assert "test_counter" in metrics
        assert metrics["test_counter"]["type"] == MetricType.COUNTER

    def test_list_gauges(self) -> None:
        """Listing includes gauges."""
        registry = MetricsRegistry()
        registry.gauge("test_gauge", 42.0)
        metrics = registry.list_metrics()
        assert "test_gauge" in metrics
        assert metrics["test_gauge"]["type"] == MetricType.GAUGE

    def test_list_histograms(self) -> None:
        """Listing includes histograms."""
        registry = MetricsRegistry()
        registry.histogram("test_hist", 10.0)
        metrics = registry.list_metrics()
        assert "test_hist" in metrics
        assert metrics["test_hist"]["type"] == MetricType.HISTOGRAM


class TestReset:
    """Tests for reset operation."""

    def test_reset_clears_counters(self) -> None:
        """Reset clears all counter values."""
        registry = MetricsRegistry()
        registry.increment("test", value=5.0)
        registry.reset()
        assert registry.get_counter("test") == 0.0

    def test_reset_clears_gauges(self) -> None:
        """Reset clears all gauge values."""
        registry = MetricsRegistry()
        registry.gauge("test", 42.0)
        registry.reset()
        assert registry.get_gauge("test") == 0.0

    def test_reset_clears_histograms(self) -> None:
        """Reset clears all histogram values."""
        registry = MetricsRegistry()
        registry.histogram("test", 10.0)
        registry.reset()
        assert registry.get_histogram_values("test") == []

    def test_reset_clears_all(self) -> None:
        """Reset clears all metric types."""
        registry = MetricsRegistry()
        registry.increment("counter")
        registry.gauge("gauge", 1.0)
        registry.histogram("hist", 1.0)
        registry.reset()
        assert registry.list_metrics() == {}


class TestRegister:
    """Tests for metric registration."""

    def test_register_with_help(self) -> None:
        """Register sets help text for export."""
        registry = MetricsRegistry()
        registry.register("test_metric", MetricType.COUNTER, "A test counter")
        registry.increment("test_metric")
        output = registry.export_prometheus()
        assert "A test counter" in output


class TestPrometheusExport:
    """Tests for Prometheus text format export."""

    def test_export_empty(self) -> None:
        """Empty registry exports empty string."""
        registry = MetricsRegistry()
        assert registry.export_prometheus() == ""

    def test_export_counter(self) -> None:
        """Counter exported in Prometheus format."""
        registry = MetricsRegistry()
        registry.increment("http_requests_total")
        output = registry.export_prometheus()
        assert "# TYPE http_requests_total counter" in output
        assert "http_requests_total 1" in output

    def test_export_counter_with_tags(self) -> None:
        """Counter with tags exported with labels."""
        registry = MetricsRegistry()
        registry.increment("http_requests_total", tags={"method": "POST", "status": "200"})
        output = registry.export_prometheus()
        assert 'method="POST"' in output
        assert 'status="200"' in output

    def test_export_gauge(self) -> None:
        """Gauge exported in Prometheus format."""
        registry = MetricsRegistry()
        registry.gauge("temperature", 36.6)
        output = registry.export_prometheus()
        assert "# TYPE temperature gauge" in output
        assert "temperature 36.6" in output

    def test_export_histogram(self) -> None:
        """Histogram exported with count and sum."""
        registry = MetricsRegistry()
        registry.histogram("duration_ms", 100.0)
        registry.histogram("duration_ms", 200.0)
        output = registry.export_prometheus()
        assert "# TYPE duration_ms histogram" in output
        assert "duration_ms_count 2" in output
        assert "duration_ms_sum 300" in output

    def test_export_includes_help(self) -> None:
        """Export includes HELP lines."""
        registry = MetricsRegistry()
        registry.increment("test")
        output = registry.export_prometheus()
        assert "# HELP test" in output
