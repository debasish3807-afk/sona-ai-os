"""Tests for the plugin registry infrastructure."""

import pytest

from sona_plugins.domain.capability import PluginCapability, PluginCapabilityType
from sona_plugins.domain.models import PluginManifest, PluginStatus
from sona_plugins.infrastructure.plugin_lifecycle import PluginLifecycleManager
from sona_plugins.infrastructure.plugin_loader import PluginLoader
from sona_plugins.infrastructure.plugin_registry import PluginRegistry
from sona_plugins.infrastructure.plugin_repository import PluginRepository


def _make_manifest(plugin_id: str = "test-plugin") -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name="Test Plugin",
        version="1.0.0",
        author="Test Author",
        description="A test plugin",
        entry_point="test.module.TestPlugin",
        permissions=[],
    )


class DummyPlugin:
    """Dummy plugin class for testing."""

    async def activate(self) -> None:
        pass

    async def deactivate(self) -> None:
        pass

    async def health_check(self) -> bool:
        return True

    async def get_capabilities(self) -> list[str]:
        return ["test"]


@pytest.fixture
def registry() -> PluginRegistry:
    repo = PluginRepository()
    lifecycle = PluginLifecycleManager()
    loader = PluginLoader()
    loader.register_entry_point("test.module.TestPlugin", DummyPlugin)
    return PluginRegistry(repo, lifecycle, loader)


class TestPluginRegistryInstall:
    """Tests for plugin installation."""

    @pytest.mark.asyncio
    async def test_install_returns_plugin_id(self, registry: PluginRegistry) -> None:
        result = await registry.install(_make_manifest())
        assert result == "test-plugin"

    @pytest.mark.asyncio
    async def test_install_duplicate_raises(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        with pytest.raises(ValueError, match="already exists"):
            await registry.install(_make_manifest())

    @pytest.mark.asyncio
    async def test_install_invalid_manifest_raises(self, registry: PluginRegistry) -> None:
        manifest = PluginManifest(
            plugin_id="",
            name="",
            version="bad",
            author="",
            description="",
            entry_point="",
            permissions=[],
        )
        with pytest.raises(ValueError, match="Invalid manifest"):
            await registry.install(manifest)

    @pytest.mark.asyncio
    async def test_installed_plugin_is_inactive(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        plugins = await registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].status == PluginStatus.INACTIVE


class TestPluginRegistryUninstall:
    """Tests for plugin uninstallation."""

    @pytest.mark.asyncio
    async def test_uninstall_existing(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        result = await registry.uninstall("test-plugin")
        assert result is True

    @pytest.mark.asyncio
    async def test_uninstall_nonexistent(self, registry: PluginRegistry) -> None:
        result = await registry.uninstall("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_uninstall_removes_from_list(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        await registry.uninstall("test-plugin")
        plugins = await registry.list_plugins()
        assert len(plugins) == 0


class TestPluginRegistryActivate:
    """Tests for plugin activation."""

    @pytest.mark.asyncio
    async def test_activate_installed_plugin(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        result = await registry.activate("test-plugin")
        assert result is True

    @pytest.mark.asyncio
    async def test_activate_sets_status_active(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        await registry.activate("test-plugin")
        plugin = await registry.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.status == PluginStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_activate_nonexistent_returns_false(self, registry: PluginRegistry) -> None:
        result = await registry.activate("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_activate_already_active(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        await registry.activate("test-plugin")
        result = await registry.activate("test-plugin")
        assert result is True


class TestPluginRegistryDeactivate:
    """Tests for plugin deactivation."""

    @pytest.mark.asyncio
    async def test_deactivate_active_plugin(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        await registry.activate("test-plugin")
        result = await registry.deactivate("test-plugin")
        assert result is True

    @pytest.mark.asyncio
    async def test_deactivate_sets_inactive(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        await registry.activate("test-plugin")
        await registry.deactivate("test-plugin")
        plugin = await registry.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.status == PluginStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent(self, registry: PluginRegistry) -> None:
        result = await registry.deactivate("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_deactivate_inactive_returns_false(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest())
        result = await registry.deactivate("test-plugin")
        assert result is False


class TestPluginRegistryList:
    """Tests for listing plugins."""

    @pytest.mark.asyncio
    async def test_list_empty(self, registry: PluginRegistry) -> None:
        plugins = await registry.list_plugins()
        assert plugins == []

    @pytest.mark.asyncio
    async def test_list_multiple(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest("plugin-a"))
        await registry.install(_make_manifest("plugin-b"))
        plugins = await registry.list_plugins()
        assert len(plugins) == 2

    @pytest.mark.asyncio
    async def test_find_by_capability(self, registry: PluginRegistry) -> None:
        await registry.install(_make_manifest("tool-plugin"))
        cap = PluginCapability(name="search", capability_type=PluginCapabilityType.TOOL)
        registry.register_capabilities("tool-plugin", [cap])
        result = registry.find_by_capability(PluginCapabilityType.TOOL)
        assert "tool-plugin" in result
