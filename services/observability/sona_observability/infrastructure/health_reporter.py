"""Health reporter for aggregated service health.

Provides detailed health status from all registered services
for the /health/detailed endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HealthStatus(StrEnum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ServiceHealth:
    """Health status for a single service component."""

    name: str
    status: HealthStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class HealthReporter:
    """Aggregates health status from all registered service components.

    Provides a unified health view for the /health/detailed endpoint.
    Overall status is determined by the worst individual component status.
    """

    def __init__(self) -> None:
        self._components: dict[str, ServiceHealth] = {}

    def register_component(self, name: str) -> None:
        """Register a health-checked component.

        Args:
            name: The component name.
        """
        self._components[name] = ServiceHealth(name=name, status=HealthStatus.HEALTHY)

    def update_status(
        self,
        name: str,
        status: HealthStatus,
        message: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Update the health status of a component.

        Args:
            name: The component name.
            status: The new health status.
            message: Optional status message.
            details: Optional detail data.
        """
        self._components[name] = ServiceHealth(
            name=name,
            status=status,
            message=message,
            details=details or {},
        )

    @property
    def overall_status(self) -> HealthStatus:
        """Compute the overall health status.

        Returns the worst status among all registered components.
        """
        if not self._components:
            return HealthStatus.HEALTHY

        statuses = [c.status for c in self._components.values()]
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def detailed_report(self) -> dict[str, Any]:
        """Generate a detailed health report.

        Returns:
            Dictionary with overall status and per-component details.
        """
        components: list[dict[str, Any]] = []
        for comp in self._components.values():
            entry: dict[str, Any] = {
                "name": comp.name,
                "status": str(comp.status),
            }
            if comp.message:
                entry["message"] = comp.message
            if comp.details:
                entry["details"] = comp.details
            components.append(entry)

        return {
            "status": str(self.overall_status),
            "components": components,
        }
