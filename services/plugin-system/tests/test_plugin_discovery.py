"""Tests for the plugin discovery system."""

import pytest

from sona_plugins.domain.capability import PluginCapability, PluginCapabilityType
from sona_plugins.domain.models import PluginManifest
from sona_plugins.infrastructure.plugin_discovery import PluginDiscovery


def _make_manifest(plugin_id: str = "test-plugin") -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name=f"Plugin {plugin_id}",
        version="1.0.0",
        author="Test",
        description="Test plugin",
        entry_point=f"plugins.{plugin_id}.Main",
        permissions=[],
    )


@pytest.fixture
def discovery() -> PluginDiscovery:
    return PluginDiscovery()


class TestPluginDiscoveryScan:
    """Tests for scanning and discovering plugins."""

    @pytest.mark.asyncio
    async def test_scan_with_manifests(self, discovery: PluginDiscovery) -> None:
        manifests = [_make_manifest("a"), _make_manifest("b")]
        discovered = await discovery.scan(manifests)
        assert len(discovered) == 2

    @pytest.mark.asyncio
    async def test_scan_empty(self, discovery: PluginDiscovery) -> None:
        discovered = await discovery.scan([])
        assert discovered == []

    @pytest.mark.asyncio
    async def test_scan_none(self, discovery: PluginDiscovery) -> None:
        discovered = await discovery.scan(None)
        assert discovered == []


class TestPluginDiscoveryRegister:
    """Tests for manual plugin registration."""

    def test_register_discovered(self, discovery: PluginDiscovery) -> None:
        manifest = _make_manifest("p1")
        result = discovery.register_discovered(manifest)
        assert result.manifest == manifest
        assert result.source == "manual"

    def test_register_with_capabilities(self, discovery: PluginDiscovery) -> None:
        manifest = _make_manifest("p1")
        caps = [PluginCapability(name="search", capability_type=PluginCapabilityType.TOOL)]
        result = discovery.register_discovered(manifest, capabilities=caps)
        assert len(result.capabilities) == 1

    def test_get_discovered(self, discovery: PluginDiscovery) -> None:
        manifest = _make_manifest("p1")
        discovery.register_discovered(manifest)
        result = discovery.get_discovered("p1")
        assert result is not None
        assert result.manifest.plugin_id == "p1"

    def test_get_discovered_none(self, discovery: PluginDiscovery) -> None:
        assert discovery.get_discovered("nonexistent") is None

    def test_get_all_discovered(self, discovery: PluginDiscovery) -> None:
        discovery.register_discovered(_make_manifest("a"))
        discovery.register_discovered(_make_manifest("b"))
        all_plugins = discovery.get_all_discovered()
        assert len(all_plugins) == 2


class TestPluginDiscoveryCapabilityLookup:
    """Tests for capability-based lookup."""

    def test_find_by_capability(self, discovery: PluginDiscovery) -> None:
        manifest = _make_manifest("tool-plugin")
        caps = [PluginCapability(name="search", capability_type=PluginCapabilityType.TOOL)]
        discovery.register_discovered(manifest, capabilities=caps)

        results = discovery.find_by_capability(PluginCapabilityType.TOOL)
        assert len(results) == 1
        assert results[0].manifest.plugin_id == "tool-plugin"

    def test_find_by_capability_empty(self, discovery: PluginDiscovery) -> None:
        results = discovery.find_by_capability(PluginCapabilityType.AGENT)
        assert results == []

    def test_find_by_capability_multiple(self, discovery: PluginDiscovery) -> None:
        for i in range(3):
            manifest = _make_manifest(f"tool-{i}")
            caps = [PluginCapability(name=f"cap-{i}", capability_type=PluginCapabilityType.TOOL)]
            discovery.register_discovered(manifest, capabilities=caps)

        results = discovery.find_by_capability(PluginCapabilityType.TOOL)
        assert len(results) == 3


class TestPluginDiscoveryRemoval:
    """Tests for removing discovered plugins."""

    def test_remove_existing(self, discovery: PluginDiscovery) -> None:
        discovery.register_discovered(_make_manifest("p1"))
        assert discovery.remove_discovered("p1") is True
        assert discovery.get_discovered("p1") is None

    def test_remove_nonexistent(self, discovery: PluginDiscovery) -> None:
        assert discovery.remove_discovered("nonexistent") is False

    def test_count(self, discovery: PluginDiscovery) -> None:
        discovery.register_discovered(_make_manifest("a"))
        discovery.register_discovered(_make_manifest("b"))
        assert discovery.count() == 2


class TestPluginDiscoverySources:
    """Tests for discovery source management."""

    def test_register_source(self, discovery: PluginDiscovery) -> None:
        discovery.register_source("/plugins")
        assert "/plugins" in discovery.get_sources()

    def test_register_duplicate_source(self, discovery: PluginDiscovery) -> None:
        discovery.register_source("/plugins")
        discovery.register_source("/plugins")
        assert len(discovery.get_sources()) == 1
