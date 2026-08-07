"""Unit tests for the PrometheusExporter infrastructure module.

Tests validate that exported text conforms to valid Prometheus
exposition format, including HELP, TYPE, metric lines, and labels.
"""

from sona_observability.infrastructure.metrics_registry import MetricsRegistry
from sona_observability.infrastructure.prometheus_exporter import PrometheusExporter


class TestPrometheusFormat:
    """Tests for Prometheus text format validity."""

    def test_export_empty_registry(self) -> None:
        """Empty registry exports empty string."""
        registry = MetricsRegistry()
        exporter = PrometheusExporter(registry)
        assert exporter.export() == ""

    def test_export_counter_has_help(self) -> None:
        """Counter export includes HELP line."""
        registry = MetricsRegistry()
        registry.increment("test_counter")
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert "# HELP test_counter" in output

    def test_export_counter_has_type(self) -> None:
        """Counter export includes TYPE counter line."""
        registry = MetricsRegistry()
        registry.increment("test_counter")
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert "# TYPE test_counter counter" in output

    def test_export_counter_has_value(self) -> None:
        """Counter export includes metric value."""
        registry = MetricsRegistry()
        registry.increment("test_counter", value=42.0)
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert "test_counter 42" in output

    def test_export_counter_with_labels(self) -> None:
        """Counter with labels exported correctly."""
        registry = MetricsRegistry()
        registry.increment(
            "http_requests_total",
            tags={"method": "POST", "path": "/v1/chat/completions", "status": "200"},
        )
        registry.increment(
            "http_requests_total",
            value=42.0,
            tags={"method": "POST", "path": "/v1/chat/completions", "status": "200"},
        )
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert 'method="POST"' in output
        assert 'path="/v1/chat/completions"' in output
        assert 'status="200"' in output

    def test_export_gauge_has_type(self) -> None:
        """Gauge export includes TYPE gauge line."""
        registry = MetricsRegistry()
        registry.gauge("temperature", 36.6)
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert "# TYPE temperature gauge" in output

    def test_export_gauge_has_value(self) -> None:
        """Gauge export includes current value."""
        registry = MetricsRegistry()
        registry.gauge("cpu_usage", 75.5)
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert "cpu_usage 75.5" in output

    def test_export_histogram_has_type(self) -> None:
        """Histogram export includes TYPE histogram line."""
        registry = MetricsRegistry()
        registry.histogram("duration_ms", 100.0)
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert "# TYPE duration_ms histogram" in output

    def test_export_histogram_has_count_and_sum(self) -> None:
        """Histogram export includes _count and _sum."""
        registry = MetricsRegistry()
        registry.histogram("duration_ms", 100.0)
        registry.histogram("duration_ms", 200.0)
        registry.histogram("duration_ms", 300.0)
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert "duration_ms_count 3" in output
        assert "duration_ms_sum 600" in output

    def test_export_ends_with_newline(self) -> None:
        """Export output ends with a newline."""
        registry = MetricsRegistry()
        registry.increment("test")
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert output.endswith("\n")

    def test_content_type(self) -> None:
        """Content type is correct Prometheus format."""
        registry = MetricsRegistry()
        exporter = PrometheusExporter(registry)
        assert exporter.content_type() == "text/plain; version=0.0.4; charset=utf-8"

    def test_export_multiple_metrics(self) -> None:
        """Multiple metrics are all exported."""
        registry = MetricsRegistry()
        registry.increment("counter_a")
        registry.gauge("gauge_b", 1.0)
        registry.histogram("hist_c", 10.0)
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        assert "counter_a" in output
        assert "gauge_b" in output
        assert "hist_c" in output

    def test_export_parseable_format(self) -> None:
        """Exported lines follow name{labels} value format."""
        registry = MetricsRegistry()
        registry.increment("requests", tags={"method": "GET"})
        exporter = PrometheusExporter(registry)
        output = exporter.export()
        lines = [line_ for line_ in output.strip().split("\n") if not line_.startswith("#")]
        for line in lines:
            # Should match: metric_name{labels} value or metric_name value
            assert " " in line  # value separator
            parts = line.split(" ")
            assert len(parts) == 2
            assert parts[1].replace(".", "").replace("-", "").isdigit() or parts[1] == "0"
