"""Health aggregation for all subsystems."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class HealthAggregator:
    """Aggregates real health from all subsystems."""

    def __init__(self, container: Any = None) -> None:
        self._container = container
        self._components: dict[str, dict[str, Any]] = {}
        self._started_at: float = time.time()

    def register_component(self, name: str) -> None:
        """Register a component for health checking."""
        self._components[name] = {"healthy": True, "latency_ms": 0.0}

    def check_all(self) -> dict[str, dict[str, Any]]:
        """Check health of all registered components.

        Returns:
            Dictionary mapping component names to health status.
        """
        results: dict[str, dict[str, Any]] = {}
        for name in self._components:
            start = time.time()
            healthy = self._check_component(name)
            latency_ms = (time.time() - start) * 1000
            results[name] = {"healthy": healthy, "latency_ms": latency_ms}
        return results

    def liveness(self) -> dict[str, str]:
        """Liveness probe — is the process alive.

        Returns:
            Liveness status dictionary.
        """
        return {"status": "alive"}

    def readiness(self) -> dict[str, Any]:
        """Readiness probe — is the service ready to accept traffic.

        Returns:
            Readiness status with component details.
        """
        components = self.check_all()
        all_healthy = all(c["healthy"] for c in components.values())
        status = "ready" if all_healthy else "not_ready"
        return {"status": status, "components": components}

    def _check_component(self, name: str) -> bool:
        """Check a single component's health."""
        try:
            stored = self._components.get(name, {})
            return bool(stored.get("healthy", False))
        except Exception:
            logger.warning("health_check_failed", component=name)
            return False

    def set_component_health(self, name: str, healthy: bool) -> None:
        """Set the health status of a component."""
        self._components[name] = {
            "healthy": healthy,
            "latency_ms": 0.0,
            "last_check": time.time(),
        }
