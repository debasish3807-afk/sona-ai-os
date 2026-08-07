"""Tests for the plugin metrics system."""

import pytest

from sona_plugins.infrastructure.plugin_metrics import PluginMetrics


@pytest.fixture
def metrics() -> PluginMetrics:
    return PluginMetrics()


class TestPluginMetricsCounters:
    """Tests for counter metrics."""

    def test_initial_counters_zero(self, metrics: PluginMetrics) -> None:
        assert metrics.get_counter("plugin_load_total") == 0
        assert metrics.get_counter("plugin_execution_total") == 0
        assert metrics.get_counter("plugin_failure_total") == 0

    def test_increment_counter(self, metrics: PluginMetrics) -> None:
        metrics.increment_counter("plugin_load_total")
        assert metrics.get_counter("plugin_load_total") == 1

    def test_increment_by_value(self, metrics: PluginMetrics) -> None:
        metrics.increment_counter("plugin_load_total", 5.0)
        assert metrics.get_counter("plugin_load_total") == 5.0

    def test_increment_multiple(self, metrics: PluginMetrics) -> None:
        metrics.increment_counter("plugin_execution_total")
        metrics.increment_counter("plugin_execution_total")
        metrics.increment_counter("plugin_execution_total")
        assert metrics.get_counter("plugin_execution_total") == 3

    def test_get_nonexistent_counter(self, metrics: PluginMetrics) -> None:
        assert metrics.get_counter("nonexistent") == 0.0


class TestPluginMetricsGauges:
    """Tests for gauge metrics."""

    def test_set_gauge(self, metrics: PluginMetrics) -> None:
        metrics.set_gauge("plugin_active_count", 5.0)
        assert metrics.get_gauge("plugin_active_count") == 5.0

    def test_gauge_overwrite(self, metrics: PluginMetrics) -> None:
        metrics.set_gauge("plugin_active_count", 5.0)
        metrics.set_gauge("plugin_active_count", 3.0)
        assert metrics.get_gauge("plugin_active_count") == 3.0

    def test_get_nonexistent_gauge(self, metrics: PluginMetrics) -> None:
        assert metrics.get_gauge("nonexistent") == 0.0


class TestPluginMetricsHistograms:
    """Tests for histogram metrics."""

    def test_record_histogram(self, metrics: PluginMetrics) -> None:
        metrics.record_histogram("plugin_duration_ms", 10.0)
        metrics.record_histogram("plugin_duration_ms", 20.0)
        stats = metrics.get_histogram_stats("plugin_duration_ms")
        assert stats["count"] == 2
        assert stats["min"] == 10.0
        assert stats["max"] == 20.0
        assert stats["avg"] == 15.0

    def test_empty_histogram(self, metrics: PluginMetrics) -> None:
        stats = metrics.get_histogram_stats("plugin_duration_ms")
        assert stats["count"] == 0

    def test_histogram_sum(self, metrics: PluginMetrics) -> None:
        metrics.record_histogram("plugin_duration_ms", 5.0)
        metrics.record_histogram("plugin_duration_ms", 15.0)
        stats = metrics.get_histogram_stats("plugin_duration_ms")
        assert stats["sum"] == 20.0


class TestPluginMetricsConvenience:
    """Tests for convenience metric methods."""

    def test_record_load(self, metrics: PluginMetrics) -> None:
        metrics.record_load("plugin-a")
        assert metrics.get_counter("plugin_load_total") == 1

    def test_record_execution_success(self, metrics: PluginMetrics) -> None:
        metrics.record_execution("plugin-a", duration_ms=50.0, success=True)
        assert metrics.get_counter("plugin_execution_total") == 1
        assert metrics.get_counter("plugin_failure_total") == 0

    def test_record_execution_failure(self, metrics: PluginMetrics) -> None:
        metrics.record_execution("plugin-a", duration_ms=50.0, success=False)
        assert metrics.get_counter("plugin_execution_total") == 1
        assert metrics.get_counter("plugin_failure_total") == 1

    def test_record_memory_usage(self, metrics: PluginMetrics) -> None:
        metrics.record_memory_usage("plugin-a", 32.5)
        stats = metrics.get_histogram_stats("plugin_memory_usage")
        assert stats["count"] == 1
        assert stats["max"] == 32.5

    def test_set_active_count(self, metrics: PluginMetrics) -> None:
        metrics.set_active_count(3)
        assert metrics.get_gauge("plugin_active_count") == 3.0


class TestPluginMetricsAll:
    """Tests for aggregate metrics retrieval."""

    def test_get_all_metrics(self, metrics: PluginMetrics) -> None:
        metrics.increment_counter("plugin_load_total")
        metrics.set_gauge("plugin_active_count", 2.0)
        all_metrics = metrics.get_all_metrics()
        assert "plugin_load_total" in all_metrics
        assert "plugin_active_count" in all_metrics

    def test_reset(self, metrics: PluginMetrics) -> None:
        metrics.increment_counter("plugin_load_total", 10.0)
        metrics.set_gauge("plugin_active_count", 5.0)
        metrics.record_histogram("plugin_duration_ms", 100.0)
        metrics.reset()
        assert metrics.get_counter("plugin_load_total") == 0
        assert metrics.get_gauge("plugin_active_count") == 0
        stats = metrics.get_histogram_stats("plugin_duration_ms")
        assert stats["count"] == 0
