"""In-memory metrics registry implementing MetricsPort.

Provides counter, gauge, and histogram metric types with tag support.
Histograms compute real percentiles from stored observation values.
"""

from __future__ import annotations

import math
from typing import Any

from sona_observability.application.ports import MetricsPort
from sona_observability.domain.models import MetricType


def _tags_key(tags: dict[str, Any] | None) -> str:
    """Create a stable string key from tags dict."""
    if not tags:
        return ""
    sorted_items = sorted(tags.items())
    return ",".join(f'{k}="{v}"' for k, v in sorted_items)


class MetricsRegistry(MetricsPort):
    """In-memory metrics registry supporting counters, gauges, and histograms.

    All metrics are stored in-memory for fast synchronous access.
    Supports tag-based dimensionality and Prometheus text format export.
    """

    def __init__(self) -> None:
        self._counters: dict[str, dict[str, float]] = {}
        self._gauges: dict[str, dict[str, float]] = {}
        self._histograms: dict[str, dict[str, list[float]]] = {}
        self._metric_help: dict[str, str] = {}
        self._metric_types: dict[str, MetricType] = {}

    def register(self, name: str, metric_type: MetricType, help_text: str = "") -> None:
        """Register a metric with a type and optional help text."""
        self._metric_types[name] = metric_type
        if help_text:
            self._metric_help[name] = help_text

    def increment(self, name: str, value: float = 1.0, tags: dict[str, Any] | None = None) -> None:
        """Increment a counter metric."""
        key = _tags_key(tags)
        if name not in self._counters:
            self._counters[name] = {}
        self._counters[name].setdefault(key, 0.0)
        self._counters[name][key] += value
        if name not in self._metric_types:
            self._metric_types[name] = MetricType.COUNTER

    def gauge(self, name: str, value: float, tags: dict[str, Any] | None = None) -> None:
        """Set a gauge metric to a specific value."""
        key = _tags_key(tags)
        if name not in self._gauges:
            self._gauges[name] = {}
        self._gauges[name][key] = value
        if name not in self._metric_types:
            self._metric_types[name] = MetricType.GAUGE

    def histogram(self, name: str, value: float, tags: dict[str, Any] | None = None) -> None:
        """Record a value in a histogram metric."""
        key = _tags_key(tags)
        if name not in self._histograms:
            self._histograms[name] = {}
        self._histograms[name].setdefault(key, [])
        self._histograms[name][key].append(value)
        if name not in self._metric_types:
            self._metric_types[name] = MetricType.HISTOGRAM

    def get_counter(self, name: str, tags: dict[str, Any] | None = None) -> float:
        """Get current counter value."""
        key = _tags_key(tags)
        return self._counters.get(name, {}).get(key, 0.0)

    def get_gauge(self, name: str, tags: dict[str, Any] | None = None) -> float:
        """Get current gauge value."""
        key = _tags_key(tags)
        return self._gauges.get(name, {}).get(key, 0.0)

    def get_histogram_values(self, name: str, tags: dict[str, Any] | None = None) -> list[float]:
        """Get all recorded histogram values."""
        key = _tags_key(tags)
        return list(self._histograms.get(name, {}).get(key, []))

    def percentile(self, name: str, p: float, tags: dict[str, Any] | None = None) -> float:
        """Compute a percentile from stored histogram values.

        Args:
            name: The histogram metric name.
            p: The percentile to compute (0-100).
            tags: Optional tags filter.

        Returns:
            The percentile value, or 0.0 if no data.
        """
        values = self.get_histogram_values(name, tags)
        if not values:
            return 0.0
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n == 1:
            return sorted_values[0]
        # Use nearest-rank method
        rank = (p / 100.0) * (n - 1)
        lower = int(math.floor(rank))
        upper = int(math.ceil(rank))
        if lower == upper:
            return sorted_values[lower]
        # Linear interpolation
        fraction = rank - lower
        return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])

    def list_metrics(self) -> dict[str, dict[str, Any]]:
        """List all metrics with their current values."""
        result: dict[str, dict[str, Any]] = {}
        for name, series in self._counters.items():
            result[name] = {"type": MetricType.COUNTER, "values": dict(series)}
        for name, series in self._gauges.items():
            result[name] = {"type": MetricType.GAUGE, "values": dict(series)}
        for name, hist_series in self._histograms.items():
            result[name] = {
                "type": MetricType.HISTOGRAM,
                "values": {k: len(v) for k, v in hist_series.items()},
            }
        return result

    def reset(self) -> None:
        """Reset all metrics to their initial state."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()

    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus text format."""
        lines: list[str] = []
        # Export counters
        for name, series in sorted(self._counters.items()):
            help_text = self._metric_help.get(name, f"Total {name}")
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} counter")
            for tags_str, value in sorted(series.items()):
                if tags_str:
                    lines.append(f"{name}{{{tags_str}}} {value:g}")
                else:
                    lines.append(f"{name} {value:g}")
        # Export gauges
        for name, series in sorted(self._gauges.items()):
            help_text = self._metric_help.get(name, f"Current {name}")
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} gauge")
            for tags_str, value in sorted(series.items()):
                if tags_str:
                    lines.append(f"{name}{{{tags_str}}} {value:g}")
                else:
                    lines.append(f"{name} {value:g}")
        # Export histograms
        for name, hist_data in sorted(self._histograms.items()):
            help_text = self._metric_help.get(name, f"Distribution of {name}")
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} histogram")
            for tags_str, values in sorted(hist_data.items()):
                count = len(values)
                total = sum(values)
                if tags_str:
                    lines.append(f"{name}_count{{{tags_str}}} {count}")
                    lines.append(f"{name}_sum{{{tags_str}}} {total:g}")
                else:
                    lines.append(f"{name}_count {count}")
                    lines.append(f"{name}_sum {total:g}")
        return "\n".join(lines) + "\n" if lines else ""
