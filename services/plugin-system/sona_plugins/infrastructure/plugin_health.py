"""Plugin health checker — monitor individual and aggregate plugin health."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger()


class HealthStatus(StrEnum):
    """Health status for a plugin."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check for a single plugin."""

    plugin_id: str
    status: HealthStatus
    message: str = ""
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    response_time_ms: float = 0.0


@dataclass
class AggregateHealth:
    """Aggregate health status across all plugins."""

    status: HealthStatus
    total: int
    healthy: int
    unhealthy: int
    degraded: int
    unknown: int
    details: list[HealthCheckResult] = field(default_factory=list)


class PluginHealthChecker:
    """Monitors plugin health status.

    Performs individual health checks and provides aggregate health views.
    Marks unhealthy plugins for potential error state transition.
    """

    def __init__(self, unhealthy_threshold: int = 3) -> None:
        self._health_status: dict[str, HealthStatus] = {}
        self._failure_counts: dict[str, int] = {}
        self._last_checks: dict[str, HealthCheckResult] = {}
        self._unhealthy_threshold = unhealthy_threshold
        self._check_handlers: dict[str, Any] = {}

    def register(self, plugin_id: str) -> None:
        """Register a plugin for health monitoring."""
        self._health_status[plugin_id] = HealthStatus.UNKNOWN
        self._failure_counts[plugin_id] = 0

    def unregister(self, plugin_id: str) -> None:
        """Remove a plugin from health monitoring."""
        self._health_status.pop(plugin_id, None)
        self._failure_counts.pop(plugin_id, None)
        self._last_checks.pop(plugin_id, None)
        self._check_handlers.pop(plugin_id, None)

    async def check(
        self, plugin_id: str, healthy: bool = True, message: str = ""
    ) -> HealthCheckResult:
        """Perform a health check for a specific plugin.

        Args:
            plugin_id: The plugin to check.
            healthy: Whether the check passed.
            message: Optional status message.

        Returns:
            HealthCheckResult with the check outcome.
        """
        if healthy:
            self._failure_counts[plugin_id] = 0
            status = HealthStatus.HEALTHY
        else:
            self._failure_counts[plugin_id] = self._failure_counts.get(plugin_id, 0) + 1
            if self._failure_counts[plugin_id] >= self._unhealthy_threshold:
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.DEGRADED

        self._health_status[plugin_id] = status
        result = HealthCheckResult(
            plugin_id=plugin_id,
            status=status,
            message=message,
        )
        self._last_checks[plugin_id] = result

        logger.debug(
            "health_check_completed",
            plugin_id=plugin_id,
            status=status,
            message=message,
        )
        return result

    def get_status(self, plugin_id: str) -> HealthStatus:
        """Get the current health status for a plugin."""
        return self._health_status.get(plugin_id, HealthStatus.UNKNOWN)

    def get_last_check(self, plugin_id: str) -> HealthCheckResult | None:
        """Get the last health check result for a plugin."""
        return self._last_checks.get(plugin_id)

    def get_aggregate_health(self) -> AggregateHealth:
        """Get aggregate health status across all monitored plugins."""
        statuses = list(self._health_status.values())
        healthy_count = statuses.count(HealthStatus.HEALTHY)
        unhealthy_count = statuses.count(HealthStatus.UNHEALTHY)
        degraded_count = statuses.count(HealthStatus.DEGRADED)
        unknown_count = statuses.count(HealthStatus.UNKNOWN)

        # Determine overall status
        if unhealthy_count > 0:
            overall = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall = HealthStatus.DEGRADED
        elif healthy_count > 0:
            overall = HealthStatus.HEALTHY
        else:
            overall = HealthStatus.UNKNOWN

        return AggregateHealth(
            status=overall,
            total=len(statuses),
            healthy=healthy_count,
            unhealthy=unhealthy_count,
            degraded=degraded_count,
            unknown=unknown_count,
            details=list(self._last_checks.values()),
        )

    def get_unhealthy_plugins(self) -> list[str]:
        """Get a list of unhealthy plugin IDs."""
        return [
            pid for pid, status in self._health_status.items() if status == HealthStatus.UNHEALTHY
        ]

    def mark_healthy(self, plugin_id: str) -> None:
        """Manually mark a plugin as healthy."""
        self._health_status[plugin_id] = HealthStatus.HEALTHY
        self._failure_counts[plugin_id] = 0

    def mark_unhealthy(self, plugin_id: str, reason: str = "") -> None:
        """Manually mark a plugin as unhealthy."""
        self._health_status[plugin_id] = HealthStatus.UNHEALTHY
        self._failure_counts[plugin_id] = self._unhealthy_threshold
