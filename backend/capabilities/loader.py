"""Capability Loader — loads, unloads, and reloads capability instances."""

from __future__ import annotations

from capabilities.base import BaseCapability
from capabilities.exceptions import CapabilityLoadError, CapabilityNotFoundError
from capabilities.registry import CapabilityRegistry
from capabilities.schemas import Capability
from config.logging import get_logger

logger = get_logger(__name__)


class CapabilityLoader:
    """Handles loading and unloading of capability instances.

    Validates schemas before loading and manages the lifecycle
    transitions during load/unload/reload operations.
    """

    async def load(self, capability_id: str, registry: CapabilityRegistry) -> BaseCapability | None:
        """Load a capability instance from the registry.

        Args:
            capability_id: The capability to load.
            registry: The capability registry.

        Returns:
            The loaded capability instance, or None if loading fails.

        Raises:
            CapabilityNotFoundError: If the capability is not registered.
            CapabilityLoadError: If validation fails.
        """
        schema = registry.get(capability_id)
        if schema is None:
            raise CapabilityNotFoundError(capability_id)

        if not self._validate(schema):
            raise CapabilityLoadError(f"Validation failed for capability '{capability_id}'")

        instance = registry.get_instance(capability_id)
        if instance is not None:
            await instance.initialize()
            logger.info("capability_loaded", capability_id=capability_id)
            return instance

        logger.warning("capability_no_instance", capability_id=capability_id)
        return None

    async def unload(self, capability_id: str, registry: CapabilityRegistry) -> bool:
        """Unload a capability, shutting down its instance.

        Returns:
            True if successfully unloaded, False otherwise.
        """
        instance = registry.get_instance(capability_id)
        if instance is None:
            return False

        await instance.shutdown()
        logger.info("capability_unloaded", capability_id=capability_id)
        return True

    async def reload(
        self, capability_id: str, registry: CapabilityRegistry
    ) -> BaseCapability | None:
        """Reload a capability by unloading then loading it.

        Returns:
            The reloaded capability instance, or None.
        """
        await self.unload(capability_id, registry)
        return await self.load(capability_id, registry)

    def _validate(self, schema: Capability) -> bool:
        """Validate that a capability schema has all required fields.

        Returns:
            True if valid, False otherwise.
        """
        if not schema.name or not schema.name.strip():
            return False
        if not schema.version or not schema.version.strip():
            return False
        if not schema.entrypoint or not schema.entrypoint.strip():
            return False
        if not schema.author or not schema.author.strip():
            return False
        return True
