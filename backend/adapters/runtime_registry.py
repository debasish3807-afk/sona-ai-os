"""Runtime Registry — manages all registered runtime services."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

from adapters.exceptions import RegistryError
from adapters.schemas import RuntimeService, ServiceStatus
from config.logging import get_logger

logger = get_logger(__name__)


class RuntimeRegistry:
    """Central registry for all runtime services.

    Provides registration, discovery, status management, heartbeat tracking,
    and dependency-aware ordering of services.
    """

    def __init__(self) -> None:
        self._services: dict[str, RuntimeService] = {}

    @property
    def count(self) -> int:
        """Total number of registered services."""
        return len(self._services)

    def register(self, service: RuntimeService) -> bool:
        """Register a new runtime service.

        Returns True if registration succeeded, False if already registered.
        """
        if service.service_id in self._services:
            logger.warning("service_already_registered", service_id=service.service_id)
            return False
        self._services[service.service_id] = service
        logger.info("service_registered", service_id=service.service_id, name=service.name)
        return True

    def deregister(self, service_id: str) -> bool:
        """Remove a service from the registry.

        Returns True if removed, False if not found.
        """
        if service_id not in self._services:
            return False
        del self._services[service_id]
        logger.info("service_deregistered", service_id=service_id)
        return True

    def get(self, service_id: str) -> RuntimeService | None:
        """Retrieve a service by ID."""
        return self._services.get(service_id)

    def list_all(self) -> list[RuntimeService]:
        """List all registered services."""
        return list(self._services.values())

    def list_running(self) -> list[RuntimeService]:
        """List only services in RUNNING status."""
        return [s for s in self._services.values() if s.status == ServiceStatus.RUNNING]

    def update_status(self, service_id: str, status: ServiceStatus) -> bool:
        """Update the status of a registered service.

        Returns True if updated, False if service not found.
        """
        service = self._services.get(service_id)
        if service is None:
            return False
        service.status = status
        logger.debug("service_status_updated", service_id=service_id, status=status.value)
        return True

    def heartbeat(self, service_id: str) -> bool:
        """Record a heartbeat for a service.

        Returns True if recorded, False if service not found.
        """
        service = self._services.get(service_id)
        if service is None:
            return False
        service.last_heartbeat = time.time()
        return True

    def get_dependency_order(self) -> list[str]:
        """Return service IDs in topological order based on dependencies.

        Services with no dependencies come first.
        Raises RegistryError if a circular dependency is detected.
        """
        in_degree: dict[str, int] = dict.fromkeys(self._services, 0)
        adjacency: dict[str, list[str]] = {sid: [] for sid in self._services}

        for sid, svc in self._services.items():
            for dep in svc.dependencies:
                if dep in self._services:
                    adjacency[dep].append(sid)
                    in_degree[sid] += 1

        queue: deque[str] = deque(sid for sid, deg in in_degree.items() if deg == 0)
        order: list[str] = []

        while queue:
            current = queue.popleft()
            order.append(current)
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self._services):
            raise RegistryError("circular dependency detected among services")

        return order

    def get_status_summary(self) -> dict[str, Any]:
        """Summarize service statuses."""
        total = len(self._services)
        running = sum(1 for s in self._services.values() if s.status == ServiceStatus.RUNNING)
        stopped = sum(1 for s in self._services.values() if s.status == ServiceStatus.STOPPED)
        failed = sum(1 for s in self._services.values() if s.status == ServiceStatus.FAILED)
        return {
            "total": total,
            "running": running,
            "stopped": stopped,
            "failed": failed,
        }
