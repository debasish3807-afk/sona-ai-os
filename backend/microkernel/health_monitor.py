"""Health Monitor — tracks component health and reports system status."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HealthCheck:
    """Result of a health check for a single component."""

    component: str
    healthy: bool
    latency_ms: float
    details: str = ""
    checked_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "component": self.component,
            "healthy": self.healthy,
            "latency_ms": self.latency_ms,
            "details": self.details,
            "checked_at": self.checked_at,
        }


class HealthMonitor:
    """Monitors the health of microkernel components.

    Tracks the latest health status for each registered component
    and provides summary diagnostics.
    """

    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    def register_component(self, component: str) -> None:
        """Register a component for health monitoring."""
        self._checks[component] = HealthCheck(
            component=component,
            healthy=True,
            latency_ms=0.0,
            details="registered",
        )

    def check_component(self, component: str) -> HealthCheck:
        """Return the latest health check for a component."""
        check = self._checks.get(component)
        if check is None:
            return HealthCheck(
                component=component,
                healthy=False,
                latency_ms=0.0,
                details="component not registered",
            )
        return check

    def check_all(self) -> dict[str, HealthCheck]:
        """Return health checks for all registered components."""
        return dict(self._checks)

    def update_health(
        self,
        component: str,
        healthy: bool,
        latency_ms: float,
        details: str = "",
    ) -> None:
        """Update the health status of a component."""
        self._checks[component] = HealthCheck(
            component=component,
            healthy=healthy,
            latency_ms=latency_ms,
            details=details,
            checked_at=time.time(),
        )
        if not healthy:
            logger.warning("component_unhealthy", component=component, details=details)

    def get_unhealthy(self) -> list[str]:
        """Get names of all unhealthy components."""
        return [name for name, check in self._checks.items() if not check.healthy]

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of overall system health."""
        total = len(self._checks)
        healthy_count = sum(1 for c in self._checks.values() if c.healthy)
        return {
            "total": total,
            "healthy_count": healthy_count,
            "unhealthy_count": total - healthy_count,
            "components": {name: check.to_dict() for name, check in self._checks.items()},
        }

    def is_system_healthy(self) -> bool:
        """Returns True if all components are healthy."""
        if not self._checks:
            return True
        return all(check.healthy for check in self._checks.values())
