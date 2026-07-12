"""Capability Manager — main orchestrator for the Dynamic Capability Fabric."""

from __future__ import annotations

from typing import Any

from capabilities.base import BaseCapability
from capabilities.events import CapabilityEvent, CapabilityEventType
from capabilities.exceptions import CapabilityNotFoundError
from capabilities.health import HealthMonitor
from capabilities.loader import CapabilityLoader
from capabilities.registry import CapabilityRegistry
from capabilities.schemas import Capability
from capabilities.selector import CapabilitySelector
from config.logging import get_logger

logger = get_logger(__name__)


class CapabilityManager:
    """Main orchestrator for the Dynamic Capability Fabric.

    Coordinates registration, activation, suspension, execution,
    and removal of capabilities through the registry, loader,
    health monitor, and selector subsystems.
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
        loader: CapabilityLoader,
        health_monitor: HealthMonitor,
        selector: CapabilitySelector,
    ) -> None:
        self._registry = registry
        self._loader = loader
        self._health_monitor = health_monitor
        self._selector = selector
        self._events: list[CapabilityEvent] = []

    def _emit(self, event_type: CapabilityEventType, capability_id: str, name: str = "") -> None:
        event = CapabilityEvent(
            event_type=event_type,
            capability_id=capability_id,
            capability_name=name,
        )
        self._events.append(event)

    def register_capability(
        self, schema: Capability, instance: BaseCapability | None = None
    ) -> str:
        """Register a new capability.

        Returns:
            The capability ID.
        """
        self._registry.register(schema, instance)
        self._emit(CapabilityEventType.REGISTERED, schema.capability_id, schema.name)
        logger.info("manager_registered", capability_id=schema.capability_id)
        return schema.capability_id

    async def activate(self, capability_id: str) -> bool:
        """Activate a registered capability by loading it."""
        schema = self._registry.get(capability_id)
        if schema is None:
            raise CapabilityNotFoundError(capability_id)

        instance = await self._loader.load(capability_id, self._registry)
        if instance is not None:
            schema.is_active = True
            schema.health_status = "healthy"
            self._emit(CapabilityEventType.ACTIVATED, capability_id, schema.name)
            return True
        return False

    async def suspend(self, capability_id: str) -> bool:
        """Suspend an active capability."""
        schema = self._registry.get(capability_id)
        if schema is None:
            raise CapabilityNotFoundError(capability_id)

        schema.is_active = False
        schema.health_status = "suspended"
        self._emit(CapabilityEventType.FAILED, capability_id, schema.name)
        logger.info("manager_suspended", capability_id=capability_id)
        return True

    async def resume(self, capability_id: str) -> bool:
        """Resume a suspended capability."""
        schema = self._registry.get(capability_id)
        if schema is None:
            raise CapabilityNotFoundError(capability_id)

        schema.is_active = True
        schema.health_status = "healthy"
        self._emit(CapabilityEventType.ACTIVATED, capability_id, schema.name)
        logger.info("manager_resumed", capability_id=capability_id)
        return True

    async def remove(self, capability_id: str) -> bool:
        """Remove a capability from the fabric entirely."""
        schema = self._registry.get(capability_id)
        if schema is None:
            return False

        await self._loader.unload(capability_id, self._registry)
        self._registry.unregister(capability_id)
        self._emit(CapabilityEventType.REMOVED, capability_id, schema.name)
        logger.info("manager_removed", capability_id=capability_id)
        return True

    async def execute(self, capability_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a capability with the given context."""
        instance = self._registry.get_instance(capability_id)
        if instance is None:
            raise CapabilityNotFoundError(capability_id)

        try:
            result = await instance.execute(context)
            self._emit(CapabilityEventType.EXECUTED, capability_id)
            return result
        except Exception as exc:
            self._emit(CapabilityEventType.FAILED, capability_id)
            logger.error("manager_execute_failed", capability_id=capability_id, error=str(exc))
            return {"success": False, "error": str(exc)}

    def get_status(self) -> dict[str, Any]:
        """Get a summary of all capabilities in the fabric."""
        capabilities = self._registry.list_all()
        return {
            "total": len(capabilities),
            "active": sum(1 for c in capabilities if c.is_active),
            "suspended": sum(1 for c in capabilities if not c.is_active),
            "capabilities": [c.to_dict() for c in capabilities],
            "recent_events": [e.to_dict() for e in self._events[-20:]],
        }
