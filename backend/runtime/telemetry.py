"""Runtime telemetry collection and reporting."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class RuntimeTelemetry:
    """Collects runtime telemetry metrics."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record(self, metric: str, value: float, component: str = "runtime") -> None:
        """Record a telemetry metric."""
        self._records.append(
            {
                "metric": metric,
                "value": value,
                "component": component,
                "timestamp": time.time(),
            }
        )
        logger.debug("telemetry_recorded", metric=metric, value=value, component=component)

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of all recorded metrics."""
        if not self._records:
            return {"total_records": 0, "metrics": {}}

        metrics: dict[str, list[float]] = {}
        for rec in self._records:
            name = rec["metric"]
            if name not in metrics:
                metrics[name] = []
            metrics[name].append(rec["value"])

        summary: dict[str, Any] = {}
        for name, values in metrics.items():
            summary[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

        return {
            "total_records": len(self._records),
            "metrics": summary,
        }

    def reset(self) -> None:
        """Clear all telemetry records."""
        count = len(self._records)
        self._records.clear()
        logger.info("telemetry_reset", cleared=count)
