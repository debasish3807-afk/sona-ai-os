"""Plugin registry — manages plugin installation, activation, and lifecycle."""

from __future__ import annotations

import structlog

from sona_plugins.application.ports import PluginPort, PluginRegistryPort
from sona_plugins.domain.capability import PluginCapability, PluginCapabilityType
from sona_plugins.domain.lifecycle import PluginLifecycleState
from sona_plugins.domain.models import PluginInstance, PluginManifest, PluginStatus
from sona_plugins.infrastructure.plugin_lifecycle import PluginLifecycleManager
from sona_plugins.infrastructure.plugin_loader import PluginLoader
from sona_plugins.infrastructure.plugin_repository import PluginRepository

logger = structlog.get_logger()


class PluginRegistry(PluginRegistryPort):
    """Concrete implementation of PluginRegistryPort.

    Manages the full lifecycle of plugins including installation,
    activation, deactivation, and uninstallation.
    """

    def __init__(
        self,
        repository: PluginRepository,
        lifecycle: PluginLifecycleManager,
        loader: PluginLoader,
    ) -> None:
        self._repository = repository
        self._lifecycle = lifecycle
        self._loader = loader
        self._capabilities: dict[str, list[PluginCapability]] = {}
        self._plugin_instances: dict[str, PluginPort] = {}

    async def install(self, manifest: PluginManifest) -> str:
        """Install a plugin from its manifest.

        Raises:
            ValueError: If the plugin already exists or manifest is invalid.
        """
        plugin_id = manifest.plugin_id

        if await self._repository.exists(plugin_id):
            raise ValueError(f"Plugin already exists: {plugin_id}")

        # Validate manifest
        errors = self._loader.validate_manifest(manifest)
        if errors:
            raise ValueError(f"Invalid manifest: {'; '.join(errors)}")

        # Create instance
        instance = PluginInstance(
            manifest=manifest,
            status=PluginStatus.INACTIVE,
        )
        await self._repository.add(instance)
        self._lifecycle.register(plugin_id)

        # Transition through discovery -> install -> verify
        self._lifecycle.transition(plugin_id, PluginLifecycleState.INSTALLED)
        self._lifecycle.transition(plugin_id, PluginLifecycleState.VERIFIED)

        logger.info("plugin_installed", plugin_id=plugin_id, name=manifest.name)
        return plugin_id

    async def uninstall(self, plugin_id: str) -> bool:
        """Uninstall a plugin by ID."""
        instance = await self._repository.get(plugin_id)
        if instance is None:
            return False

        # Deactivate if active
        if instance.status == PluginStatus.ACTIVE:
            await self.deactivate(plugin_id)

        # Unload if loaded
        if self._loader.is_loaded(plugin_id):
            await self._loader.unload(plugin_id)

        # Remove from repository
        await self._repository.remove(plugin_id)
        self._lifecycle.unregister(plugin_id)
        self._capabilities.pop(plugin_id, None)
        self._plugin_instances.pop(plugin_id, None)

        logger.info("plugin_uninstalled", plugin_id=plugin_id)
        return True

    async def activate(self, plugin_id: str) -> bool:
        """Activate an installed plugin."""
        instance = await self._repository.get(plugin_id)
        if instance is None:
            return False

        if instance.status == PluginStatus.ACTIVE:
            return True

        # Load the plugin
        try:
            current_state = self._lifecycle.get_state(plugin_id)
            if current_state == PluginLifecycleState.VERIFIED:
                self._lifecycle.transition(plugin_id, PluginLifecycleState.LOADED)

            plugin = await self._loader.load(instance.manifest)
            self._plugin_instances[plugin_id] = plugin

            current_state = self._lifecycle.get_state(plugin_id)
            if current_state == PluginLifecycleState.LOADED:
                self._lifecycle.transition(plugin_id, PluginLifecycleState.INITIALIZED)
                self._lifecycle.transition(plugin_id, PluginLifecycleState.STARTED)
                self._lifecycle.transition(plugin_id, PluginLifecycleState.RUNNING)

            # Activate the plugin
            if hasattr(plugin, "activate"):
                await plugin.activate()

            instance.status = PluginStatus.ACTIVE
            instance.error = None
            await self._repository.update(instance)

            logger.info("plugin_activated", plugin_id=plugin_id)
            return True

        except Exception as exc:
            instance.status = PluginStatus.ERROR
            instance.error = str(exc)
            await self._repository.update(instance)
            logger.error("plugin_activation_failed", plugin_id=plugin_id, error=str(exc))
            return False

    async def deactivate(self, plugin_id: str) -> bool:
        """Deactivate an active plugin."""
        instance = await self._repository.get(plugin_id)
        if instance is None:
            return False

        if instance.status != PluginStatus.ACTIVE:
            return False

        # Deactivate the plugin
        plugin = self._plugin_instances.get(plugin_id)
        if plugin and hasattr(plugin, "deactivate"):
            await plugin.deactivate()

        # Transition lifecycle
        current_state = self._lifecycle.get_state(plugin_id)
        if current_state == PluginLifecycleState.RUNNING:
            self._lifecycle.transition(plugin_id, PluginLifecycleState.STOPPING)
            self._lifecycle.transition(plugin_id, PluginLifecycleState.STOPPED)

        instance.status = PluginStatus.INACTIVE
        await self._repository.update(instance)

        logger.info("plugin_deactivated", plugin_id=plugin_id)
        return True

    async def list_plugins(self) -> list[PluginInstance]:
        """List all installed plugins."""
        return await self._repository.get_all()

    async def get_plugin(self, plugin_id: str) -> PluginInstance | None:
        """Get a specific plugin instance."""
        return await self._repository.get(plugin_id)

    async def get_plugin_port(self, plugin_id: str) -> PluginPort | None:
        """Get the PluginPort instance for a loaded plugin."""
        return self._plugin_instances.get(plugin_id)

    def register_capabilities(self, plugin_id: str, capabilities: list[PluginCapability]) -> None:
        """Register capabilities for a plugin."""
        self._capabilities[plugin_id] = capabilities

    def get_capabilities(self, plugin_id: str) -> list[PluginCapability]:
        """Get registered capabilities for a plugin."""
        return self._capabilities.get(plugin_id, [])

    def find_by_capability(self, capability_type: PluginCapabilityType) -> list[str]:
        """Find plugins that provide a specific capability type."""
        result: list[str] = []
        for pid, caps in self._capabilities.items():
            for cap in caps:
                if cap.capability_type == capability_type:
                    result.append(pid)
                    break
        return result

    async def get_active_plugins(self) -> list[PluginInstance]:
        """Get all active plugins."""
        return await self._repository.get_by_status(PluginStatus.ACTIVE)
