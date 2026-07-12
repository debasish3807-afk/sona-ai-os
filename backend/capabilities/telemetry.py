"""Capability Telemetry — execution metrics and statistics tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionRecord:
    """A single execution record."""

    success: bool
    duration_ms: float
    tokens_used: int
    cost: float


class CapabilityTelemetry:
    """Tracks execution metrics for capabilities.

    Records execution success, duration, token usage, and cost
    to provide aggregate statistics per capability.
    """

    def __init__(self) -> None:
        self._records: dict[str, list[ExecutionRecord]] = {}

    def record_execution(
        self,
        capability_id: str,
        success: bool,
        duration_ms: float,
        tokens_used: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Record an execution event.

        Args:
            capability_id: The capability that was executed.
            success: Whether execution succeeded.
            duration_ms: Execution duration in milliseconds.
            tokens_used: Number of tokens consumed.
            cost: Cost of execution.
        """
        if capability_id not in self._records:
            self._records[capability_id] = []

        record = ExecutionRecord(
            success=success,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost=cost,
        )
        self._records[capability_id].append(record)

    def get_stats(self, capability_id: str) -> dict[str, Any]:
        """Get aggregate statistics for a capability.

        Args:
            capability_id: The capability ID.

        Returns:
            Dictionary with total_executions, success_rate, avg_latency, total_cost.
        """
        records = self._records.get(capability_id, [])
        if not records:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_latency": 0.0,
                "total_cost": 0.0,
            }

        total = len(records)
        successes = sum(1 for r in records if r.success)
        avg_latency = sum(r.duration_ms for r in records) / total
        total_cost = sum(r.cost for r in records)

        return {
            "total_executions": total,
            "success_rate": successes / total if total > 0 else 0.0,
            "avg_latency": round(avg_latency, 2),
            "total_cost": round(total_cost, 6),
        }

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all tracked capabilities.

        Returns:
            Dictionary mapping capability_id to stats.
        """
        return {cap_id: self.get_stats(cap_id) for cap_id in self._records}

    def reset(self, capability_id: str) -> None:
        """Reset telemetry data for a capability.

        Args:
            capability_id: The capability to reset.
        """
        self._records.pop(capability_id, None)
        logger.info("telemetry_reset", capability_id=capability_id)
