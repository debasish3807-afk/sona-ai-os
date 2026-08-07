"""Plugin discovery — scan directories and register discovered plugins."""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from sona_plugins.domain.capability import PluginCapability, PluginCapabilityType
from sona_plugins.domain.models import PluginManifest

logger = structlog.get_logger()


@dataclass
class DiscoveredPlugin:
    """Represents a plugin discovered during scanning."""

    manifest: PluginManifest
    source: str = "directory"
    capabilities: list[PluginCapability] = field(default_factory=list)


class PluginDiscovery:
    """Discovers plugins from configured sources.

    Supports:
    - Directory scanning for plugin manifests
    - Capability-based lookup
    - Registration of discovered plugins
    """

    def __init__(self) -> None:
        self._discovered: dict[str, DiscoveredPlugin] = {}
        self._capability_index: dict[PluginCapabilityType, list[str]] = {}
        self._sources: list[str] = []

    def register_source(self, source: str) -> None:
        """Register a directory or source path for plugin discovery."""
        if source not in self._sources:
            self._sources.append(source)
            logger.info("discovery_source_registered", source=source)

    async def scan(self, manifests: list[PluginManifest] | None = None) -> list[DiscoveredPlugin]:
        """Scan for plugins and return discovered plugins.

        In this implementation, plugins are registered via manifests directly.
        In production, this would scan filesystem directories.

        Args:
            manifests: List of manifests to discover (simulates directory scan).

        Returns:
            List of discovered plugins.
        """
        discovered: list[DiscoveredPlugin] = []

        if manifests:
            for manifest in manifests:
                plugin = DiscoveredPlugin(
                    manifest=manifest,
                    source="scan",
                )
                self._discovered[manifest.plugin_id] = plugin
                discovered.append(plugin)
                logger.info(
                    "plugin_discovered",
                    plugin_id=manifest.plugin_id,
                    name=manifest.name,
                )

        return discovered

    def register_discovered(
        self,
        manifest: PluginManifest,
        capabilities: list[PluginCapability] | None = None,
        source: str = "manual",
    ) -> DiscoveredPlugin:
        """Manually register a discovered plugin.

        Args:
            manifest: The plugin manifest.
            capabilities: Optional list of capabilities the plugin provides.
            source: The discovery source identifier.

        Returns:
            The DiscoveredPlugin record.
        """
        caps = capabilities or []
        plugin = DiscoveredPlugin(
            manifest=manifest,
            source=source,
            capabilities=caps,
        )
        self._discovered[manifest.plugin_id] = plugin

        # Update capability index
        for cap in caps:
            if cap.capability_type not in self._capability_index:
                self._capability_index[cap.capability_type] = []
            if manifest.plugin_id not in self._capability_index[cap.capability_type]:
                self._capability_index[cap.capability_type].append(manifest.plugin_id)

        logger.info(
            "plugin_registered_discovered",
            plugin_id=manifest.plugin_id,
            capabilities=len(caps),
        )
        return plugin

    def get_discovered(self, plugin_id: str) -> DiscoveredPlugin | None:
        """Get a discovered plugin by ID."""
        return self._discovered.get(plugin_id)

    def get_all_discovered(self) -> list[DiscoveredPlugin]:
        """Get all discovered plugins."""
        return list(self._discovered.values())

    def find_by_capability(self, capability_type: PluginCapabilityType) -> list[DiscoveredPlugin]:
        """Find plugins that provide a specific capability type."""
        plugin_ids = self._capability_index.get(capability_type, [])
        return [self._discovered[pid] for pid in plugin_ids if pid in self._discovered]

    def remove_discovered(self, plugin_id: str) -> bool:
        """Remove a discovered plugin."""
        if plugin_id not in self._discovered:
            return False

        plugin = self._discovered.pop(plugin_id)
        # Clean capability index
        for cap in plugin.capabilities:
            if cap.capability_type in self._capability_index:
                ids = self._capability_index[cap.capability_type]
                if plugin_id in ids:
                    ids.remove(plugin_id)

        return True

    def count(self) -> int:
        """Return the number of discovered plugins."""
        return len(self._discovered)

    def get_sources(self) -> list[str]:
        """Get registered discovery sources."""
        return list(self._sources)
