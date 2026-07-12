"""Telemetry — metrics collection and reporting for the microkernel."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TelemetryRecord:
    """A single telemetry metric record."""

    metric: str
    value: float
    unit: str
    component: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "metric": self.metric,
            "value": self.value,
            "unit": self.unit,
            "component": self.component,
            "timestamp": self.timestamp,
        }


class MicrokernelTelemetry:
    """Collects and reports telemetry metrics for the microkernel.

    Tracks counters, records timestamped metrics, and provides
    aggregated summaries for observability.
    """

    def __init__(self) -> None:
        self._records: list[TelemetryRecord] = []
        self._counters: dict[str, int] = {}

    def record(self, metric: str, value: float, unit: str, component: str) -> None:
        """Record a metric value."""
        record = TelemetryRecord(
            metric=metric,
            value=value,
            unit=unit,
            component=component,
        )
        self._records.append(record)

    def increment(self, counter_name: str) -> None:
        """Increment a named counter."""
        self._counters[counter_name] = self._counters.get(counter_name, 0) + 1

    def get_metric(
        self,
        metric: str,
        component: str | None = None,
        limit: int = 100,
    ) -> list[TelemetryRecord]:
        """Retrieve records for a given metric, optionally filtered by component."""
        results: list[TelemetryRecord] = []
        for record in reversed(self._records):
            if record.metric == metric:
                if component is None or record.component == component:
                    results.append(record)
            if len(results) >= limit:
                break
        return results

    def get_counters(self) -> dict[str, int]:
        """Return all counters."""
        return dict(self._counters)

    def get_summary(self) -> dict[str, Any]:
        """Get a telemetry summary."""
        return {
            "total_records": len(self._records),
            "counters": dict(self._counters),
            "last_record_at": self._records[-1].timestamp if self._records else None,
        }

    def reset(self) -> None:
        """Reset all telemetry data."""
        self._records.clear()
        self._counters.clear()
        logger.info("telemetry_reset")
