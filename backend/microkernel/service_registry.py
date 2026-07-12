"""Service Registry — tracks and discovers microkernel services."""

from __future__ import annotations

import time

from config.logging import get_logger
from microkernel.schemas import ServiceInfo

logger = get_logger(__name__)


class ServiceRegistry:
    """Registry for microkernel services with health tracking and discovery.

    Services register themselves and periodically send heartbeats.
    The registry enables capability-based discovery and health monitoring.
    """

    def __init__(self) -> None:
        self._services: dict[str, ServiceInfo] = {}

    def register(self, service: ServiceInfo) -> bool:
        """Register a new service. Returns True if successful."""
        if service.service_id in self._services:
            logger.warning("service_already_registered", service_id=service.service_id)
            return False

        self._services[service.service_id] = service
        logger.info("service_registered", service_id=service.service_id, name=service.name)
        return True

    def deregister(self, service_id: str) -> bool:
        """Remove a service from the registry."""
        if service_id not in self._services:
            return False

        del self._services[service_id]
        logger.info("service_deregistered", service_id=service_id)
        return True

    def get(self, service_id: str) -> ServiceInfo | None:
        """Retrieve a service by ID."""
        return self._services.get(service_id)

    def discover(self, capability: str) -> list[ServiceInfo]:
        """Find services that provide a given capability."""
        return [
            svc for svc in self._services.values() if capability in svc.capabilities and svc.health
        ]

    def list_all(self) -> list[ServiceInfo]:
        """List all registered services."""
        return list(self._services.values())

    def heartbeat(self, service_id: str) -> bool:
        """Update the heartbeat timestamp for a service."""
        service = self._services.get(service_id)
        if service is None:
            return False

        service.last_heartbeat = time.time()
        return True

    def check_health(self, service_id: str) -> bool:
        """Check if a service is healthy based on its heartbeat."""
        service = self._services.get(service_id)
        if service is None:
            return False
        return service.health

    def get_unhealthy(self, timeout_seconds: float = 60.0) -> list[str]:
        """Get service IDs that have missed their heartbeat deadline."""
        now = time.time()
        unhealthy: list[str] = []
        for svc in self._services.values():
            if now - svc.last_heartbeat > timeout_seconds:
                svc.health = False
                unhealthy.append(svc.service_id)
        return unhealthy

    @property
    def count(self) -> int:
        """Number of registered services."""
        return len(self._services)
