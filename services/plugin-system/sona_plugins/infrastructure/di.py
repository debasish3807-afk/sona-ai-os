"""Dependency injection factory for the plugin runtime."""

from __future__ import annotations

from sona_plugins.infrastructure.builtin_plugins import (
    BUILTIN_MANIFESTS,
    EchoPlugin,
    FormatterPlugin,
    MetricsPlugin,
    TimerPlugin,
)
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
from sona_plugins.infrastructure.plugin_repository import PluginRepository
from sona_plugins.infrastructure.plugin_runtime import PluginRuntime
from sona_plugins.infrastructure.plugin_sandbox import SandboxConfig


def create_plugin_runtime(
    sandbox_config: SandboxConfig | None = None,
) -> PluginRuntime:
    """Create a fully-configured PluginRuntime instance.

    All components are wired together with default configurations.
    """
    repository = PluginRepository()
    lifecycle = PluginLifecycleManager()
    loader = PluginLoader()
    permission_manager = PluginPermissionManager()
    dependency_resolver = PluginDependencyResolver()
    config_manager = PluginConfigManager()
    discovery = PluginDiscovery()
    health_checker = PluginHealthChecker()
    metrics = PluginMetrics()

    # Register built-in plugin entry points
    loader.register_entry_point(
        "sona_plugins.infrastructure.builtin_plugins.EchoPlugin", EchoPlugin
    )
    loader.register_entry_point(
        "sona_plugins.infrastructure.builtin_plugins.TimerPlugin", TimerPlugin
    )
    loader.register_entry_point(
        "sona_plugins.infrastructure.builtin_plugins.MetricsPlugin", MetricsPlugin
    )
    loader.register_entry_point(
        "sona_plugins.infrastructure.builtin_plugins.FormatterPlugin", FormatterPlugin
    )

    return PluginRuntime(
        repository=repository,
        lifecycle=lifecycle,
        loader=loader,
        permission_manager=permission_manager,
        sandbox_config=sandbox_config,
        dependency_resolver=dependency_resolver,
        config_manager=config_manager,
        discovery=discovery,
        health_checker=health_checker,
        metrics=metrics,
    )


async def create_plugin_runtime_with_builtins(
    sandbox_config: SandboxConfig | None = None,
) -> PluginRuntime:
    """Create a PluginRuntime with all built-in plugins installed and activated.

    This is the recommended way to create a runtime for production use.
    """
    runtime = create_plugin_runtime(sandbox_config)

    # Install and activate all built-in plugins
    for manifest in BUILTIN_MANIFESTS:
        await runtime.install(manifest)
        await runtime.activate(manifest.plugin_id)

    return runtime
