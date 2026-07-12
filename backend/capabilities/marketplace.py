"""Marketplace — in-memory capability marketplace for discovery."""

from __future__ import annotations

from typing import Any

from capabilities.registry import CapabilityRegistry
from capabilities.schemas import Capability, CapabilityCategory
from config.logging import get_logger

logger = get_logger(__name__)


class Marketplace:
    """In-memory capability marketplace for browsing and installation.

    Provides a catalog of available capabilities that can be
    searched, inspected, and installed into the registry.
    """

    def __init__(self) -> None:
        self._catalog: dict[str, dict[str, Any]] = {}

    def search(self, query: str, category: str | None = None) -> list[dict[str, Any]]:
        """Search the marketplace catalog.

        Args:
            query: Search term (substring match on name/description).
            category: Optional category filter.

        Returns:
            List of matching catalog entries.
        """
        results: list[dict[str, Any]] = []
        query_lower = query.lower()
        for entry in self._catalog.values():
            if category and entry.get("category") != category:
                continue
            name = entry.get("name", "").lower()
            desc = entry.get("description", "").lower()
            if query_lower in name or query_lower in desc:
                results.append(entry)
        return results

    def get_details(self, capability_id: str) -> dict[str, Any] | None:
        """Get detailed information about a marketplace entry.

        Args:
            capability_id: The capability ID to look up.

        Returns:
            Catalog entry dict, or None if not found.
        """
        return self._catalog.get(capability_id)

    def install(self, capability_id: str, registry: CapabilityRegistry) -> bool:
        """Install a capability from the marketplace into the registry.

        Args:
            capability_id: The capability to install.
            registry: The target registry.

        Returns:
            True if installed successfully.
        """
        entry = self._catalog.get(capability_id)
        if entry is None:
            return False

        schema = Capability(
            capability_id=capability_id,
            name=entry.get("name", ""),
            version=entry.get("version", "1.0.0"),
            description=entry.get("description", ""),
            author=entry.get("author", "marketplace"),
            category=CapabilityCategory(entry.get("category", "tool")),
            entrypoint=entry.get("entrypoint", ""),
        )
        registry.register(schema)
        logger.info("marketplace_installed", capability_id=capability_id)
        return True

    def list_installed(self, registry: CapabilityRegistry) -> list[dict[str, Any]]:
        """List capabilities that are installed in the registry.

        Returns:
            List of installed capability dicts.
        """
        installed: list[dict[str, Any]] = []
        for schema in registry.list_all():
            if schema.capability_id in self._catalog:
                installed.append(schema.to_dict())
        return installed

    def list_available(self) -> list[dict[str, Any]]:
        """List all available capabilities in the marketplace.

        Returns:
            List of all catalog entries.
        """
        return list(self._catalog.values())
