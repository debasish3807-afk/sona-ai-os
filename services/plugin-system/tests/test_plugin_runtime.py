"""Tests for the plugin runtime — full integration."""

import pytest

from sona_plugins.domain.capability import PluginCapability, PluginCapabilityType
from sona_plugins.domain.models import PluginManifest, PluginStatus
from sona_plugins.domain.permissions import PluginPermission
from sona_plugins.infrastructure.di import (
    create_plugin_runtime,
    create_plugin_runtime_with_builtins,
)
from sona_plugins.infrastructure.plugin_runtime import PluginRuntime


def _make_manifest(plugin_id: str = "test-plugin") -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name="Test Plugin",
        version="1.0.0",
        author="Test",
        description="Test",
        entry_point="sona_plugins.infrastructure.builtin_plugins.EchoPlugin",
        permissions=[],
    )


@pytest.fixture
def runtime() -> PluginRuntime:
    return create_plugin_runtime()


class TestRuntimeInstallActivate:
    """Tests for runtime install/activate flow."""

    @pytest.mark.asyncio
    async def test_install_plugin(self, runtime: PluginRuntime) -> None:
        pid = await runtime.install(_make_manifest())
        assert pid == "test-plugin"

    @pytest.mark.asyncio
    async def test_install_and_activate(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        result = await runtime.activate("test-plugin")
        assert result is True

    @pytest.mark.asyncio
    async def test_activate_sets_status(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        plugin = await runtime.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.status == PluginStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_deactivate_plugin(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        result = await runtime.deactivate("test-plugin")
        assert result is True

    @pytest.mark.asyncio
    async def test_uninstall_plugin(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        result = await runtime.uninstall("test-plugin")
        assert result is True
        plugins = await runtime.list_plugins()
        assert len(plugins) == 0


class TestRuntimeExecution:
    """Tests for plugin execution."""

    @pytest.mark.asyncio
    async def test_execute_echo(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        execution = await runtime.execute_plugin("test-plugin", "execute", "hello")
        assert execution.success is True
        assert execution.result == "hello"

    @pytest.mark.asyncio
    async def test_execute_not_loaded_raises(self, runtime: PluginRuntime) -> None:
        with pytest.raises(ValueError, match="not loaded"):
            await runtime.execute_plugin("nonexistent", "execute")

    @pytest.mark.asyncio
    async def test_execute_invalid_action_raises(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        with pytest.raises(ValueError, match="no action"):
            await runtime.execute_plugin("test-plugin", "nonexistent_method")

    @pytest.mark.asyncio
    async def test_execute_records_metrics(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        await runtime.execute_plugin("test-plugin", "execute", "test")
        assert runtime.metrics.get_counter("plugin_execution_total") >= 1

    @pytest.mark.asyncio
    async def test_execute_emits_event(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        await runtime.execute_plugin("test-plugin", "execute", "test")
        events = runtime.drain_events()
        assert len(events) >= 1
        assert events[0].plugin_id == "test-plugin"


class TestRuntimeWithBuiltins:
    """Tests for runtime with built-in plugins."""

    @pytest.mark.asyncio
    async def test_create_with_builtins(self) -> None:
        runtime = await create_plugin_runtime_with_builtins()
        plugins = await runtime.list_plugins()
        assert len(plugins) == 4

    @pytest.mark.asyncio
    async def test_builtins_are_active(self) -> None:
        runtime = await create_plugin_runtime_with_builtins()
        plugins = await runtime.list_plugins()
        for plugin in plugins:
            assert plugin.status == PluginStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_execute_builtin_echo(self) -> None:
        runtime = await create_plugin_runtime_with_builtins()
        execution = await runtime.execute_plugin("builtin-echo", "execute", "hi")
        assert execution.success is True
        assert execution.result == "hi"

    @pytest.mark.asyncio
    async def test_execute_builtin_formatter(self) -> None:
        runtime = await create_plugin_runtime_with_builtins()
        execution = await runtime.execute_plugin("builtin-formatter", "to_uppercase", "hello")
        assert execution.success is True
        assert execution.result == "HELLO"


class TestRuntimeHealth:
    """Tests for runtime health checking."""

    @pytest.mark.asyncio
    async def test_check_health_active_plugin(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        healthy = await runtime.check_health("test-plugin")
        assert healthy is True

    @pytest.mark.asyncio
    async def test_check_health_not_loaded(self, runtime: PluginRuntime) -> None:
        healthy = await runtime.check_health("nonexistent")
        assert healthy is False


class TestRuntimePermissions:
    """Tests for runtime permission management."""

    @pytest.mark.asyncio
    async def test_grant_permission(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        runtime.grant_permission("test-plugin", PluginPermission.NETWORK_HTTP)
        assert runtime.permission_manager.has_permission(
            "test-plugin", PluginPermission.NETWORK_HTTP
        )

    @pytest.mark.asyncio
    async def test_grant_multiple_permissions(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        perms = frozenset({PluginPermission.NETWORK_HTTP, PluginPermission.DATABASE_READ})
        runtime.grant_permissions("test-plugin", perms)
        assert runtime.permission_manager.has_permission(
            "test-plugin", PluginPermission.NETWORK_HTTP
        )
        assert runtime.permission_manager.has_permission(
            "test-plugin", PluginPermission.DATABASE_READ
        )


class TestRuntimeCapabilities:
    """Tests for runtime capability management."""

    @pytest.mark.asyncio
    async def test_register_capabilities(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        caps = [PluginCapability(name="search", capability_type=PluginCapabilityType.TOOL)]
        runtime.register_capabilities("test-plugin", caps)
        found = runtime.find_plugins_by_capability(PluginCapabilityType.TOOL)
        assert "test-plugin" in found

    @pytest.mark.asyncio
    async def test_find_no_matching_capability(self, runtime: PluginRuntime) -> None:
        found = runtime.find_plugins_by_capability(PluginCapabilityType.AGENT)
        assert found == []


class TestRuntimeListPlugins:
    """Tests for listing plugins."""

    @pytest.mark.asyncio
    async def test_list_empty(self, runtime: PluginRuntime) -> None:
        plugins = await runtime.list_plugins()
        assert plugins == []

    @pytest.mark.asyncio
    async def test_list_after_install(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest("a"))
        await runtime.install(_make_manifest("b"))
        plugins = await runtime.list_plugins()
        assert len(plugins) == 2

    @pytest.mark.asyncio
    async def test_get_specific_plugin(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest("specific"))
        plugin = await runtime.get_plugin("specific")
        assert plugin is not None
        assert plugin.manifest.plugin_id == "specific"
