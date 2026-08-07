"""In-memory repository for plugin metadata, state, and configuration."""

from __future__ import annotations

import structlog

from sona_plugins.domain.lifecycle import PluginLifecycleState
from sona_plugins.domain.models import PluginInstance, PluginManifest, PluginStatus

logger = structlog.get_logger()


class PluginRepository:
    """In-memory storage for plugin instances and their state.

    Provides CRUD operations for plugin metadata, lifecycle state,
    and configuration persistence.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginInstance] = {}
        self._lifecycle_states: dict[str, PluginLifecycleState] = {}
        self._configs: dict[str, dict[str, object]] = {}

    async def add(self, instance: PluginInstance) -> None:
        """Add a plugin instance to the repository."""
        plugin_id = instance.manifest.plugin_id
        if plugin_id in self._plugins:
            raise ValueError(f"Plugin already exists: {plugin_id}")
        self._plugins[plugin_id] = instance
        self._lifecycle_states[plugin_id] = PluginLifecycleState.DISCOVERED
        logger.info("plugin_added", plugin_id=plugin_id)

    async def get(self, plugin_id: str) -> PluginInstance | None:
        """Retrieve a plugin instance by ID."""
        return self._plugins.get(plugin_id)

    async def get_all(self) -> list[PluginInstance]:
        """Retrieve all stored plugin instances."""
        return list(self._plugins.values())

    async def update(self, instance: PluginInstance) -> None:
        """Update an existing plugin instance."""
        plugin_id = instance.manifest.plugin_id
        if plugin_id not in self._plugins:
            raise ValueError(f"Plugin not found: {plugin_id}")
        self._plugins[plugin_id] = instance

    async def remove(self, plugin_id: str) -> bool:
        """Remove a plugin instance from the repository."""
        if plugin_id not in self._plugins:
            return False
        del self._plugins[plugin_id]
        self._lifecycle_states.pop(plugin_id, None)
        self._configs.pop(plugin_id, None)
        logger.info("plugin_removed", plugin_id=plugin_id)
        return True

    async def exists(self, plugin_id: str) -> bool:
        """Check if a plugin exists in the repository."""
        return plugin_id in self._plugins

    async def get_lifecycle_state(self, plugin_id: str) -> PluginLifecycleState | None:
        """Get the lifecycle state for a plugin."""
        return self._lifecycle_states.get(plugin_id)

    async def set_lifecycle_state(self, plugin_id: str, state: PluginLifecycleState) -> None:
        """Set the lifecycle state for a plugin."""
        if plugin_id not in self._plugins:
            raise ValueError(f"Plugin not found: {plugin_id}")
        self._lifecycle_states[plugin_id] = state

    async def get_config(self, plugin_id: str) -> dict[str, object]:
        """Get configuration for a plugin."""
        return self._configs.get(plugin_id, {})

    async def set_config(self, plugin_id: str, config: dict[str, object]) -> None:
        """Set configuration for a plugin."""
        self._configs[plugin_id] = config

    async def get_by_status(self, status: PluginStatus) -> list[PluginInstance]:
        """Get all plugins with a given status."""
        return [p for p in self._plugins.values() if p.status == status]

    async def get_by_lifecycle_state(self, state: PluginLifecycleState) -> list[PluginInstance]:
        """Get all plugins in a given lifecycle state."""
        return [
            self._plugins[pid]
            for pid, s in self._lifecycle_states.items()
            if s == state and pid in self._plugins
        ]

    async def count(self) -> int:
        """Return the total number of plugins in the repository."""
        return len(self._plugins)

    async def clear(self) -> None:
        """Remove all plugins from the repository."""
        self._plugins.clear()
        self._lifecycle_states.clear()
        self._configs.clear()

    async def get_manifest(self, plugin_id: str) -> PluginManifest | None:
        """Get the manifest for a specific plugin."""
        instance = self._plugins.get(plugin_id)
        return instance.manifest if instance else None
