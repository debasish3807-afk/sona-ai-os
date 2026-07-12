"""Capability Registry — central store for all registered capabilities."""

from __future__ import annotations

from capabilities.base import BaseCapability
from capabilities.exceptions import CapabilityConflictError
from capabilities.schemas import Capability, CapabilityCategory
from config.logging import get_logger

logger = get_logger(__name__)


class CapabilityRegistry:
    """Central registry for capability schemas and instances.

    Stores capability metadata alongside optional live instances,
    supporting lookup, filtering, and search operations.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, tuple[Capability, BaseCapability | None]] = {}

    def register(
        self, capability_schema: Capability, instance: BaseCapability | None = None
    ) -> None:
        """Register a capability schema with an optional live instance.

        Args:
            capability_schema: The capability metadata.
            instance: Optional live capability instance.

        Raises:
            CapabilityConflictError: If a capability with the same ID is already registered.
        """
        cap_id = capability_schema.capability_id
        if cap_id in self._capabilities:
            raise CapabilityConflictError(f"Capability '{cap_id}' is already registered")
        self._capabilities[cap_id] = (capability_schema, instance)
        logger.info("capability_registered", capability_id=cap_id, name=capability_schema.name)

    def unregister(self, capability_id: str) -> bool:
        """Remove a capability from the registry.

        Returns:
            True if removed, False if not found.
        """
        if capability_id in self._capabilities:
            del self._capabilities[capability_id]
            logger.info("capability_unregistered", capability_id=capability_id)
            return True
        return False

    def get(self, capability_id: str) -> Capability | None:
        """Get a capability schema by ID."""
        entry = self._capabilities.get(capability_id)
        return entry[0] if entry else None

    def get_instance(self, capability_id: str) -> BaseCapability | None:
        """Get a live capability instance by ID."""
        entry = self._capabilities.get(capability_id)
        return entry[1] if entry else None

    def list_all(self) -> list[Capability]:
        """Return all registered capability schemas."""
        return [schema for schema, _ in self._capabilities.values()]

    def filter_by(
        self,
        category: CapabilityCategory | None = None,
        tags: list[str] | None = None,
        min_confidence: float = 0.0,
    ) -> list[Capability]:
        """Filter capabilities by category, tags, and minimum confidence.

        Args:
            category: Optional category filter.
            tags: Optional tag filter (any match).
            min_confidence: Minimum confidence threshold.

        Returns:
            List of matching capability schemas.
        """
        results: list[Capability] = []
        for schema, _ in self._capabilities.values():
            if category is not None and schema.category != category:
                continue
            if tags and not any(tag in schema.tags for tag in tags):
                continue
            if schema.confidence < min_confidence:
                continue
            results.append(schema)
        return results

    def search(self, query: str) -> list[Capability]:
        """Search capabilities by name, description, or tags.

        Args:
            query: Search term (case-insensitive substring match).

        Returns:
            List of matching capability schemas.
        """
        query_lower = query.lower()
        results: list[Capability] = []
        for schema, _ in self._capabilities.values():
            if (
                query_lower in schema.name.lower()
                or query_lower in schema.description.lower()
                or any(query_lower in tag.lower() for tag in schema.tags)
            ):
                results.append(schema)
        return results

    def has(self, capability_id: str) -> bool:
        """Check if a capability is registered."""
        return capability_id in self._capabilities

    @property
    def count(self) -> int:
        """Number of registered capabilities."""
        return len(self._capabilities)
