"""Plugin metrics — track plugin performance and resource usage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog

logger = structlog.get_logger()


@dataclass
class MetricEntry:
    """A single metric data point."""

    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    labels: dict[str, str] = field(default_factory=dict)


class PluginMetrics:
    """Tracks plugin runtime metrics.

    Counters:
    - plugin_load_total: Number of plugin loads
    - plugin_execution_total: Number of plugin executions
    - plugin_failure_total: Number of plugin failures

    Gauges:
    - plugin_duration_ms: Execution duration in milliseconds
    - plugin_memory_usage: Memory usage in MB
    - plugin_active_count: Number of currently active plugins
    """

    def __init__(self) -> None:
        self._counters: dict[str, float] = {
            "plugin_load_total": 0,
            "plugin_execution_total": 0,
            "plugin_failure_total": 0,
        }
        self._gauges: dict[str, float] = {
            "plugin_active_count": 0,
        }
        self._histograms: dict[str, list[float]] = {
            "plugin_duration_ms": [],
            "plugin_memory_usage": [],
        }
        self._history: list[MetricEntry] = []

    def increment_counter(self, name: str, value: float = 1.0, **labels: str) -> None:
        """Increment a counter metric."""
        if name not in self._counters:
            self._counters[name] = 0
        self._counters[name] += value
        self._history.append(
            MetricEntry(value=self._counters[name], labels={"metric": name, **labels})
        )

    def set_gauge(self, name: str, value: float, **labels: str) -> None:
        """Set a gauge metric to a specific value."""
        self._gauges[name] = value
        self._history.append(MetricEntry(value=value, labels={"metric": name, **labels}))

    def record_histogram(self, name: str, value: float, **labels: str) -> None:
        """Record a value in a histogram metric."""
        if name not in self._histograms:
            self._histograms[name] = []
        self._histograms[name].append(value)
        self._history.append(MetricEntry(value=value, labels={"metric": name, **labels}))

    def get_counter(self, name: str) -> float:
        """Get the current value of a counter."""
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> float:
        """Get the current value of a gauge."""
        return self._gauges.get(name, 0.0)

    def get_histogram_stats(self, name: str) -> dict[str, float]:
        """Get statistics for a histogram metric."""
        values = self._histograms.get(name, [])
        if not values:
            return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0, "sum": 0.0}
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
        }

    # Convenience methods for plugin-specific metrics

    def record_load(self, plugin_id: str) -> None:
        """Record a plugin load event."""
        self.increment_counter("plugin_load_total", plugin_id=plugin_id)
        logger.debug("metric_plugin_load", plugin_id=plugin_id)

    def record_execution(self, plugin_id: str, duration_ms: float, success: bool = True) -> None:
        """Record a plugin execution event."""
        self.increment_counter("plugin_execution_total", plugin_id=plugin_id)
        self.record_histogram("plugin_duration_ms", duration_ms, plugin_id=plugin_id)
        if not success:
            self.increment_counter("plugin_failure_total", plugin_id=plugin_id)
        logger.debug(
            "metric_plugin_execution",
            plugin_id=plugin_id,
            duration_ms=duration_ms,
            success=success,
        )

    def record_memory_usage(self, plugin_id: str, memory_mb: float) -> None:
        """Record plugin memory usage."""
        self.record_histogram("plugin_memory_usage", memory_mb, plugin_id=plugin_id)

    def set_active_count(self, count: int) -> None:
        """Set the number of active plugins."""
        self.set_gauge("plugin_active_count", float(count))

    def get_all_metrics(self) -> dict[str, float | dict[str, float]]:
        """Get a snapshot of all metrics."""
        result: dict[str, float | dict[str, float]] = {}
        for name, value in self._counters.items():
            result[name] = value
        for name, value in self._gauges.items():
            result[name] = value
        for name in self._histograms:
            result[name] = self.get_histogram_stats(name)
        return result

    def reset(self) -> None:
        """Reset all metrics."""
        for key in self._counters:
            self._counters[key] = 0
        for key in self._gauges:
            self._gauges[key] = 0
        for key in self._histograms:
            self._histograms[key] = []
        self._history.clear()
