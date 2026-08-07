"""Unit tests for Plugin System abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest
from application.ports import PluginPort, PluginRegistryPort
from domain.models import PluginInstance, PluginManifest, PluginStatus


class TestPluginPort:
    """Tests for the PluginPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify PluginPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            PluginPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = PluginPort.__abstractmethods__
        assert "activate" in abstract_methods
        assert "deactivate" in abstract_methods
        assert "get_capabilities" in abstract_methods
        assert "health_check" in abstract_methods

    def test_abstract_method_count(self) -> None:
        """Verify exactly 4 abstract methods are defined."""
        assert len(PluginPort.__abstractmethods__) == 4

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcretePlugin(PluginPort):
            async def activate(self) -> None:
                pass

            async def deactivate(self) -> None:
                pass

            async def get_capabilities(self) -> list[str]:
                return ["search", "summarize"]

            async def health_check(self) -> bool:
                return True

        plugin = ConcretePlugin()
        assert isinstance(plugin, PluginPort)

    def test_partial_implementation_raises(self) -> None:
        """Verify partial implementation cannot be instantiated."""

        class PartialPlugin(PluginPort):
            async def activate(self) -> None:
                pass

            async def deactivate(self) -> None:
                pass

            # Missing get_capabilities and health_check

        with pytest.raises(TypeError):
            PartialPlugin()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_activate_is_callable(self) -> None:
        """Test that activate() can be called on a concrete implementation."""

        class MockPlugin(PluginPort):
            def __init__(self) -> None:
                self.activated = False

            async def activate(self) -> None:
                self.activated = True

            async def deactivate(self) -> None:
                self.activated = False

            async def get_capabilities(self) -> list[str]:
                return ["capability_a"]

            async def health_check(self) -> bool:
                return self.activated

        plugin = MockPlugin()
        assert not plugin.activated
        await plugin.activate()
        assert plugin.activated

    @pytest.mark.asyncio
    async def test_deactivate_is_callable(self) -> None:
        """Test that deactivate() can be called on a concrete implementation."""

        class MockPlugin(PluginPort):
            def __init__(self) -> None:
                self.active = True

            async def activate(self) -> None:
                self.active = True

            async def deactivate(self) -> None:
                self.active = False

            async def get_capabilities(self) -> list[str]:
                return []

            async def health_check(self) -> bool:
                return self.active

        plugin = MockPlugin()
        await plugin.deactivate()
        assert not plugin.active

    @pytest.mark.asyncio
    async def test_get_capabilities_returns_list(self) -> None:
        """Test that get_capabilities() returns a list of strings."""

        class MockPlugin(PluginPort):
            async def activate(self) -> None:
                pass

            async def deactivate(self) -> None:
                pass

            async def get_capabilities(self) -> list[str]:
                return ["search", "translate", "summarize"]

            async def health_check(self) -> bool:
                return True

        plugin = MockPlugin()
        capabilities = await plugin.get_capabilities()
        assert capabilities == ["search", "translate", "summarize"]
        assert isinstance(capabilities, list)

    @pytest.mark.asyncio
    async def test_health_check_returns_bool(self) -> None:
        """Test that health_check() returns a boolean."""

        class MockPlugin(PluginPort):
            async def activate(self) -> None:
                pass

            async def deactivate(self) -> None:
                pass

            async def get_capabilities(self) -> list[str]:
                return []

            async def health_check(self) -> bool:
                return True

        plugin = MockPlugin()
        result = await plugin.health_check()
        assert result is True
        assert isinstance(result, bool)


class TestPluginRegistryPort:
    """Tests for the PluginRegistryPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify PluginRegistryPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            PluginRegistryPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = PluginRegistryPort.__abstractmethods__
        assert "install" in abstract_methods
        assert "uninstall" in abstract_methods
        assert "activate" in abstract_methods
        assert "deactivate" in abstract_methods
        assert "list_plugins" in abstract_methods

    def test_abstract_method_count(self) -> None:
        """Verify exactly 5 abstract methods are defined."""
        assert len(PluginRegistryPort.__abstractmethods__) == 5

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteRegistry(PluginRegistryPort):
            async def install(self, manifest: PluginManifest) -> str:
                return manifest.plugin_id

            async def uninstall(self, plugin_id: str) -> bool:
                return True

            async def activate(self, plugin_id: str) -> bool:
                return True

            async def deactivate(self, plugin_id: str) -> bool:
                return True

            async def list_plugins(self) -> list[PluginInstance]:
                return []

        registry = ConcreteRegistry()
        assert isinstance(registry, PluginRegistryPort)

    def test_partial_implementation_raises(self) -> None:
        """Verify partial implementation cannot be instantiated."""

        class PartialRegistry(PluginRegistryPort):
            async def install(self, manifest: PluginManifest) -> str:
                return manifest.plugin_id

            # Missing uninstall, activate, deactivate, list_plugins

        with pytest.raises(TypeError):
            PartialRegistry()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_install_returns_plugin_id(self) -> None:
        """Test that install() returns the plugin_id."""

        class MockRegistry(PluginRegistryPort):
            async def install(self, manifest: PluginManifest) -> str:
                return manifest.plugin_id

            async def uninstall(self, plugin_id: str) -> bool:
                return True

            async def activate(self, plugin_id: str) -> bool:
                return True

            async def deactivate(self, plugin_id: str) -> bool:
                return True

            async def list_plugins(self) -> list[PluginInstance]:
                return []

        registry = MockRegistry()
        manifest = PluginManifest(
            plugin_id="weather-plugin",
            name="Weather",
            version="1.0.0",
            author="Dev",
            description="Weather info",
            entry_point="plugins.weather.Main",
            permissions=["network"],
        )
        result = await registry.install(manifest)
        assert result == "weather-plugin"
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_uninstall_returns_bool(self) -> None:
        """Test that uninstall() returns a boolean."""

        class MockRegistry(PluginRegistryPort):
            async def install(self, manifest: PluginManifest) -> str:
                return manifest.plugin_id

            async def uninstall(self, plugin_id: str) -> bool:
                return plugin_id == "existing-plugin"

            async def activate(self, plugin_id: str) -> bool:
                return True

            async def deactivate(self, plugin_id: str) -> bool:
                return True

            async def list_plugins(self) -> list[PluginInstance]:
                return []

        registry = MockRegistry()
        assert await registry.uninstall("existing-plugin") is True
        assert await registry.uninstall("nonexistent") is False

    @pytest.mark.asyncio
    async def test_list_plugins_returns_instances(self) -> None:
        """Test that list_plugins() returns a list of PluginInstance."""

        class MockRegistry(PluginRegistryPort):
            async def install(self, manifest: PluginManifest) -> str:
                return manifest.plugin_id

            async def uninstall(self, plugin_id: str) -> bool:
                return True

            async def activate(self, plugin_id: str) -> bool:
                return True

            async def deactivate(self, plugin_id: str) -> bool:
                return True

            async def list_plugins(self) -> list[PluginInstance]:
                manifest = PluginManifest(
                    plugin_id="test-plugin",
                    name="Test",
                    version="1.0.0",
                    author="Dev",
                    description="Test plugin",
                    entry_point="plugins.test.Main",
                    permissions=[],
                )
                return [
                    PluginInstance(manifest=manifest, status=PluginStatus.ACTIVE),
                    PluginInstance(
                        manifest=manifest,
                        status=PluginStatus.ERROR,
                        error="Connection timeout",
                    ),
                ]

        registry = MockRegistry()
        plugins = await registry.list_plugins()
        assert len(plugins) == 2
        assert plugins[0].status == PluginStatus.ACTIVE
        assert plugins[1].status == PluginStatus.ERROR
        assert plugins[1].error == "Connection timeout"

    @pytest.mark.asyncio
    async def test_activate_returns_bool(self) -> None:
        """Test that activate() returns a boolean."""

        class MockRegistry(PluginRegistryPort):
            async def install(self, manifest: PluginManifest) -> str:
                return manifest.plugin_id

            async def uninstall(self, plugin_id: str) -> bool:
                return True

            async def activate(self, plugin_id: str) -> bool:
                return plugin_id == "known-plugin"

            async def deactivate(self, plugin_id: str) -> bool:
                return True

            async def list_plugins(self) -> list[PluginInstance]:
                return []

        registry = MockRegistry()
        assert await registry.activate("known-plugin") is True
        assert await registry.activate("unknown-plugin") is False

    @pytest.mark.asyncio
    async def test_deactivate_returns_bool(self) -> None:
        """Test that deactivate() returns a boolean."""

        class MockRegistry(PluginRegistryPort):
            async def install(self, manifest: PluginManifest) -> str:
                return manifest.plugin_id

            async def uninstall(self, plugin_id: str) -> bool:
                return True

            async def activate(self, plugin_id: str) -> bool:
                return True

            async def deactivate(self, plugin_id: str) -> bool:
                return plugin_id == "active-plugin"

            async def list_plugins(self) -> list[PluginInstance]:
                return []

        registry = MockRegistry()
        assert await registry.deactivate("active-plugin") is True
        assert await registry.deactivate("inactive-plugin") is False
