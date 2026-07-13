"""Prometheus-compatible metrics export."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsExporter:
    """Prometheus-compatible metrics export."""

    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._labels: dict[str, dict[str, str]] = {}

    def counter(self, name: str, value: float = 1, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value
        if labels:
            self._labels[key] = labels

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric."""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        if labels:
            self._labels[key] = labels

    def histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a histogram observation."""
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        if labels:
            self._labels[key] = labels

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines: list[str] = []

        for key, value in self._counters.items():
            labels_str = self._format_labels(key)
            lines.append(f"{key.split('{')[0]}{labels_str} {value}")

        for key, value in self._gauges.items():
            labels_str = self._format_labels(key)
            lines.append(f"{key.split('{')[0]}{labels_str} {value}")

        for key, values in self._histograms.items():
            base_name = key.split("{")[0]
            labels_str = self._format_labels(key)
            count = len(values)
            total = sum(values)
            lines.append(f"{base_name}_count{labels_str} {count}")
            lines.append(f"{base_name}_sum{labels_str} {total}")

        return "\n".join(lines)

    def export_json(self) -> dict[str, Any]:
        """Export metrics as JSON dictionary."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: {"count": len(v), "sum": sum(v), "values": v}
                for k, v in self._histograms.items()
            },
        }

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Create a unique key from name and labels."""
        if not labels:
            return name
        label_parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_parts}}}"

    def _format_labels(self, key: str) -> str:
        """Format labels for Prometheus output."""
        labels = self._labels.get(key)
        if not labels:
            return ""
        parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{{{parts}}}"
