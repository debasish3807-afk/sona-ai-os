"""Health Monitor — monitors capability health and records history."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from capabilities.registry import CapabilityRegistry
from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HealthStatus:
    """Health status snapshot for a capability."""

    capability_id: str
    healthy: bool = True
    latency_ms: float = 0.0
    error_rate: float = 0.0
    memory_mb: float = 0.0
    last_check: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "capability_id": self.capability_id,
            "healthy": self.healthy,
            "latency_ms": round(self.latency_ms, 2),
            "error_rate": round(self.error_rate, 4),
            "memory_mb": round(self.memory_mb, 2),
            "last_check": self.last_check,
        }


class HealthMonitor:
    """Monitors capability health and maintains status history.

    Performs health checks on individual capabilities and tracks
    historical health data for trend analysis.
    """

    def __init__(self) -> None:
        self._history: dict[str, list[HealthStatus]] = {}

    async def check(self, capability_id: str, registry: CapabilityRegistry) -> HealthStatus:
        """Check health of a single capability.

        Args:
            capability_id: The capability to check.
            registry: The capability registry.

        Returns:
            HealthStatus with current health information.
        """
        instance = registry.get_instance(capability_id)
        schema = registry.get(capability_id)

        healthy = False
        latency_ms = 0.0

        if instance is not None:
            start = time.perf_counter()
            try:
                healthy = await instance.health()
            except Exception:
                healthy = False
            latency_ms = (time.perf_counter() - start) * 1000
        elif schema is not None:
            healthy = schema.health_status == "healthy"
            latency_ms = schema.latency_ms

        status = HealthStatus(
            capability_id=capability_id,
            healthy=healthy,
            latency_ms=latency_ms,
        )
        self._record(capability_id, status)
        return status

    async def check_all(self, registry: CapabilityRegistry) -> dict[str, HealthStatus]:
        """Check health of all registered capabilities.

        Returns:
            Dictionary mapping capability_id to HealthStatus.
        """
        results: dict[str, HealthStatus] = {}
        for schema in registry.list_all():
            status = await self.check(schema.capability_id, registry)
            results[schema.capability_id] = status
        return results

    def _record(self, capability_id: str, status: HealthStatus) -> None:
        """Record a health status entry in history."""
        if capability_id not in self._history:
            self._history[capability_id] = []
        self._history[capability_id].append(status)
        # Keep last 100 entries
        if len(self._history[capability_id]) > 100:
            self._history[capability_id] = self._history[capability_id][-100:]

    def get_history(self, capability_id: str) -> list[HealthStatus]:
        """Get health history for a capability.

        Returns:
            List of historical HealthStatus entries.
        """
        return self._history.get(capability_id, [])
