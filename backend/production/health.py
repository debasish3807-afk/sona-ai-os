"""Health check service — component-based health checking with dependency hierarchy."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HealthComponent:
    name: str
    healthy: bool = True
    message: str = ""
    last_check: float = 0.0
    dependencies: list[str] = field(default_factory=list)


@dataclass
class HealthCheckResult:
    healthy: bool
    status: str
    uptime_seconds: float
    components: dict[str, bool]
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


class HealthService:
    """Component-based health checker with dependency awareness."""

    def __init__(self) -> None:
        self._components: dict[str, HealthComponent] = {}
        self._start_time = time.time()

    def register(self, name: str, dependencies: list[str] | None = None) -> HealthComponent:
        if name not in self._components:
            self._components[name] = HealthComponent(name=name, dependencies=dependencies or [])
        return self._components[name]

    def report_healthy(self, name: str, message: str = "") -> None:
        comp = self._components.get(name)
        if comp:
            comp.healthy = True
            comp.message = message
            comp.last_check = time.time()

    def report_unhealthy(self, name: str, message: str = "") -> None:
        comp = self._components.get(name)
        if comp:
            comp.healthy = False
            comp.message = message
            comp.last_check = time.time()

    def check(self) -> HealthCheckResult:
        now = time.time()
        all_healthy = True
        components: dict[str, bool] = {}
        details: dict[str, Any] = {}

        for name, comp in self._components.items():
            components[name] = comp.healthy
            details[name] = {
                "healthy": comp.healthy,
                "message": comp.message,
                "dependencies": comp.dependencies,
                "last_check": comp.last_check,
            }
            if not comp.healthy:
                all_healthy = False

        if not self._components:
            details["startup"] = {"healthy": True, "message": "No components registered yet"}

        return HealthCheckResult(
            healthy=all_healthy,
            status="healthy" if all_healthy else "degraded",
            uptime_seconds=now - self._start_time,
            components=components,
            details=details,
            timestamp=now,
        )
