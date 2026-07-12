"""Unified Observability — health, metrics, and tracing for all subsystems."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class UnifiedHealthMonitor:
    """Aggregates health status across all subsystems into one report."""

    def __init__(self) -> None:
        self._components: dict[str, bool] = {}
        self._last_check: float = 0.0

    def register_component(self, name: str, healthy: bool = True) -> None:
        """Register a component for health tracking."""
        self._components[name] = healthy

    def update_health(self, name: str, healthy: bool) -> None:
        """Update health status for a component."""
        self._components[name] = healthy

    def is_healthy(self) -> bool:
        """Check if all components are healthy."""
        if not self._components:
            return True
        return all(self._components.values())

    def get_summary(self) -> dict[str, Any]:
        """Get a complete health summary."""
        self._last_check = time.time()
        total = len(self._components)
        healthy_count = sum(1 for v in self._components.values() if v)
        return {
            "healthy": self.is_healthy(),
            "total_components": total,
            "healthy_components": healthy_count,
            "unhealthy_components": total - healthy_count,
            "components": dict(self._components),
            "last_check": self._last_check,
        }


class UnifiedMetrics:
    """Aggregates metrics from all subsystems."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        self._counters[name] = self._counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        self._gauges[name] = value

    def record_histogram(self, name: str, value: float) -> None:
        """Record a histogram value."""
        if name not in self._histograms:
            self._histograms[name] = []
        self._histograms[name].append(value)
        # Keep last 1000 values
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self._gauges.get(name, 0.0)

    def get_histogram_stats(self, name: str) -> dict[str, float]:
        """Get histogram statistics."""
        values = self._histograms.get(name, [])
        if not values:
            return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0, "p99": 0.0}
        sorted_vals = sorted(values)
        p99_idx = int(len(sorted_vals) * 0.99)
        return {
            "count": len(values),
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "avg": sum(values) / len(values),
            "p99": sorted_vals[min(p99_idx, len(sorted_vals) - 1)],
        }

    def get_all(self) -> dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {name: self.get_histogram_stats(name) for name in self._histograms},
        }


class RequestTracer:
    """Traces requests through the system with correlation IDs."""

    def __init__(self) -> None:
        self._traces: dict[str, list[dict[str, Any]]] = {}

    def start_trace(self, correlation_id: str) -> None:
        """Start tracing a request."""
        self._traces[correlation_id] = []

    def add_span(
        self,
        correlation_id: str,
        component: str,
        operation: str,
        duration_ms: float,
        status: str = "ok",
    ) -> None:
        """Add a span to a trace."""
        if correlation_id not in self._traces:
            self._traces[correlation_id] = []
        self._traces[correlation_id].append(
            {
                "component": component,
                "operation": operation,
                "duration_ms": duration_ms,
                "status": status,
                "timestamp": time.time(),
            }
        )

    def get_trace(self, correlation_id: str) -> list[dict[str, Any]]:
        """Get all spans for a correlation ID."""
        return self._traces.get(correlation_id, [])

    def cleanup(self, max_age_seconds: float = 3600.0) -> int:
        """Remove old traces. Returns count removed."""
        now = time.time()
        to_remove: list[str] = []
        for cid, spans in self._traces.items():
            if spans and (now - spans[-1].get("timestamp", now)) > max_age_seconds or not spans:
                to_remove.append(cid)
        for cid in to_remove:
            del self._traces[cid]
        return len(to_remove)
