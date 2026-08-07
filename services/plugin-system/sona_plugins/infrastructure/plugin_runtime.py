"""Plugin runtime — top-level orchestrator combining all plugin components."""

from __future__ import annotations

from typing import Any

import structlog

from sona_plugins.application.ports import PluginRegistryPort
from sona_plugins.domain.capability import PluginCapability, PluginCapabilityType
from sona_plugins.domain.events import PluginExecutedEvent
from sona_plugins.domain.lifecycle import PluginLifecycleState
from sona_plugins.domain.models import PluginInstance, PluginManifest, PluginStatus
from sona_plugins.domain.permissions import PluginPermission
from sona_plugins.infrastructure.plugin_config_manager import PluginConfigManager
from sona_plugins.infrastructure.plugin_dependency_resolver import (
    PluginDependencyResolver,
)
from sona_plugins.infrastructure.plugin_discovery import PluginDiscovery
from sona_plugins.infrastructure.plugin_health import PluginHealthChecker
from sona_plugins.infrastructure.plugin_lifecycle import PluginLifecycleManager
from sona_plugins.infrastructure.plugin_loader import PluginLoader
from sona_plugins.infrastructure.plugin_metrics import PluginMetrics
from sona_plugins.infrastructure.plugin_permission_manager import (
    PluginPermissionManager,
)
from sona_plugins.infrastructure.plugin_registry import PluginRegistry
from sona_plugins.infrastructure.plugin_repository import PluginRepository
from sona_plugins.infrastructure.plugin_sandbox import PluginSandbox, SandboxConfig

logger = structlog.get_logger()


class PluginRuntime(PluginRegistryPort):
    """Top-level plugin runtime orchestrator.

    Combines all plugin infrastructure components and provides
    a high-level API for plugin management. Implements PluginRegistryPort.
    """

    def __init__(
        self,
        repository: PluginRepository | None = None,
        lifecycle: PluginLifecycleManager | None = None,
        loader: PluginLoader | None = None,
        permission_manager: PluginPermissionManager | None = None,
        sandbox_config: SandboxConfig | None = None,
        dependency_resolver: PluginDependencyResolver | None = None,
        config_manager: PluginConfigManager | None = None,
        discovery: PluginDiscovery | None = None,
        health_checker: PluginHealthChecker | None = None,
        metrics: PluginMetrics | None = None,
    ) -> None:
        self._repository = repository or PluginRepository()
        self._lifecycle = lifecycle or PluginLifecycleManager()
        self._loader = loader or PluginLoader()
        self._permission_manager = permission_manager or PluginPermissionManager()
        self._sandbox = PluginSandbox(self._permission_manager, sandbox_config)
        self._dependency_resolver = dependency_resolver or PluginDependencyResolver()
        self._config_manager = config_manager or PluginConfigManager()
        self._discovery = discovery or PluginDiscovery()
        self._health_checker = health_checker or PluginHealthChecker()
        self._metrics = metrics or PluginMetrics()
        self._registry = PluginRegistry(self._repository, self._lifecycle, self._loader)
        self._events: list[PluginExecutedEvent] = []

    # --- PluginRegistryPort implementation ---

    async def install(self, manifest: PluginManifest) -> str:
        """Install a plugin from its manifest."""
        # Register dependencies
        self._dependency_resolver.register(manifest.plugin_id, manifest.dependencies)

        # Register health monitoring
        self._health_checker.register(manifest.plugin_id)

        # Install via registry
        plugin_id = await self._registry.install(manifest)

        # Record metrics
        self._metrics.record_load(plugin_id)

        logger.info("runtime_plugin_installed", plugin_id=plugin_id)
        return plugin_id

    async def uninstall(self, plugin_id: str) -> bool:
        """Uninstall a plugin."""
        result = await self._registry.uninstall(plugin_id)
        if result:
            self._dependency_resolver.unregister(plugin_id)
            self._health_checker.unregister(plugin_id)
            self._permission_manager.unregister(plugin_id)
            self._config_manager.remove_config(plugin_id)
            logger.info("runtime_plugin_uninstalled", plugin_id=plugin_id)
        return result

    async def activate(self, plugin_id: str) -> bool:
        """Activate a plugin."""
        result = await self._registry.activate(plugin_id)
        if result:
            active_plugins = await self._registry.get_active_plugins()
            self._metrics.set_active_count(len(active_plugins))
            self._health_checker.mark_healthy(plugin_id)
        return result

    async def deactivate(self, plugin_id: str) -> bool:
        """Deactivate a plugin."""
        result = await self._registry.deactivate(plugin_id)
        if result:
            active_plugins = await self._registry.get_active_plugins()
            self._metrics.set_active_count(len(active_plugins))
        return result

    async def list_plugins(self) -> list[PluginInstance]:
        """List all installed plugins."""
        return await self._registry.list_plugins()

    # --- Extended API ---

    async def execute_plugin(
        self,
        plugin_id: str,
        action: str,
        *args: Any,
        required_permissions: frozenset[PluginPermission] | None = None,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a plugin action within the sandbox.

        Args:
            plugin_id: The plugin to execute.
            action: The action/method to call.
            *args: Arguments for the action.
            required_permissions: Permissions required for this action.
            timeout_seconds: Timeout override.
            **kwargs: Keyword arguments for the action.

        Returns:
            The result from the sandbox execution.
        """
        plugin = await self._registry.get_plugin_port(plugin_id)
        if plugin is None:
            raise ValueError(f"Plugin not loaded: {plugin_id}")

        handler = getattr(plugin, action, None)
        if handler is None or not callable(handler):
            raise ValueError(f"Plugin '{plugin_id}' has no action '{action}'")

        execution = await self._sandbox.execute(
            plugin_id,
            action,
            handler,
            *args,
            required_permissions=required_permissions,
            timeout_seconds=timeout_seconds,
            **kwargs,
        )

        # Record metrics
        self._metrics.record_execution(plugin_id, execution.duration_ms, execution.success)

        # Record event
        self._events.append(
            PluginExecutedEvent(
                plugin_id=plugin_id,
                action=action,
                duration_ms=execution.duration_ms,
                success=execution.success,
            )
        )

        if not execution.success:
            logger.warning(
                "runtime_execution_failed",
                plugin_id=plugin_id,
                action=action,
                error=execution.error,
            )

        return execution

    async def reload_plugin(self, plugin_id: str) -> bool:
        """Hot-reload a plugin without full restart.

        Deactivates, unloads, reloads, and reactivates the plugin.
        """
        instance = await self._repository.get(plugin_id)
        if instance is None:
            return False

        was_active = instance.status == PluginStatus.ACTIVE

        # Deactivate if active
        if was_active:
            await self.deactivate(plugin_id)

        # Unload
        await self._loader.unload(plugin_id)

        # Reload and reactivate
        if was_active:
            # Reset lifecycle for reload
            current_state = self._lifecycle.get_state(plugin_id)
            if current_state == PluginLifecycleState.STOPPED:
                self._lifecycle.transition(plugin_id, PluginLifecycleState.UNLOADING)
                self._lifecycle.transition(plugin_id, PluginLifecycleState.UNLOADED)
                self._lifecycle.transition(plugin_id, PluginLifecycleState.LOADED)
                self._lifecycle.transition(plugin_id, PluginLifecycleState.INITIALIZED)
                self._lifecycle.transition(plugin_id, PluginLifecycleState.STARTED)
                self._lifecycle.transition(plugin_id, PluginLifecycleState.RUNNING)

            # Reload plugin
            plugin = await self._loader.load(instance.manifest)
            if hasattr(plugin, "activate"):
                await plugin.activate()

            instance.status = PluginStatus.ACTIVE
            await self._repository.update(instance)

        logger.info("runtime_plugin_reloaded", plugin_id=plugin_id)
        return True

    async def check_health(self, plugin_id: str) -> bool:
        """Check the health of a specific plugin."""
        plugin = await self._registry.get_plugin_port(plugin_id)
        if plugin is None:
            await self._health_checker.check(plugin_id, healthy=False, message="Not loaded")
            return False

        try:
            healthy = await plugin.health_check()
            await self._health_checker.check(
                plugin_id,
                healthy=healthy,
                message="OK" if healthy else "Health check failed",
            )
            return healthy
        except Exception as exc:
            await self._health_checker.check(plugin_id, healthy=False, message=str(exc))
            return False

    def grant_permission(self, plugin_id: str, permission: PluginPermission) -> None:
        """Grant a permission to a plugin."""
        self._permission_manager.grant(plugin_id, permission)

    def grant_permissions(self, plugin_id: str, permissions: frozenset[PluginPermission]) -> None:
        """Grant multiple permissions to a plugin."""
        self._permission_manager.grant_all(plugin_id, permissions)

    def register_capabilities(self, plugin_id: str, capabilities: list[PluginCapability]) -> None:
        """Register capabilities for a plugin."""
        self._registry.register_capabilities(plugin_id, capabilities)

    def find_plugins_by_capability(self, capability_type: PluginCapabilityType) -> list[str]:
        """Find plugins that provide a specific capability."""
        return self._registry.find_by_capability(capability_type)

    async def get_plugin(self, plugin_id: str) -> PluginInstance | None:
        """Get a specific plugin instance."""
        return await self._registry.get_plugin(plugin_id)

    def drain_events(self) -> list[PluginExecutedEvent]:
        """Drain execution events."""
        events = list(self._events)
        self._events.clear()
        return events

    @property
    def metrics(self) -> PluginMetrics:
        """Access the metrics component."""
        return self._metrics

    @property
    def health_checker(self) -> PluginHealthChecker:
        """Access the health checker component."""
        return self._health_checker

    @property
    def sandbox(self) -> PluginSandbox:
        """Access the sandbox component."""
        return self._sandbox

    @property
    def config_manager(self) -> PluginConfigManager:
        """Access the config manager component."""
        return self._config_manager

    @property
    def dependency_resolver(self) -> PluginDependencyResolver:
        """Access the dependency resolver."""
        return self._dependency_resolver

    @property
    def discovery(self) -> PluginDiscovery:
        """Access the discovery component."""
        return self._discovery

    @property
    def permission_manager(self) -> PluginPermissionManager:
        """Access the permission manager."""
        return self._permission_manager
