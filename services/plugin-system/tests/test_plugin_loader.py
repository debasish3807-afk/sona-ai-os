"""Tests for the plugin loader."""

import pytest

from sona_plugins.domain.models import PluginManifest
from sona_plugins.infrastructure.plugin_loader import (
    PluginLoader,
    PluginLoadError,
)


class DummyPlugin:
    """Dummy plugin for testing."""

    pass


class FailingPlugin:
    """Plugin that fails to initialize."""

    def __init__(self) -> None:
        raise RuntimeError("Init failed")


def _make_manifest(
    plugin_id: str = "test-plugin",
    entry_point: str = "test.module.DummyPlugin",
    version: str = "1.0.0",
) -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name="Test Plugin",
        version=version,
        author="Test Author",
        description="A test plugin",
        entry_point=entry_point,
        permissions=[],
    )


class TestPluginLoaderLoad:
    """Tests for loading plugins."""

    @pytest.mark.asyncio
    async def test_load_registered_plugin(self) -> None:
        loader = PluginLoader()
        loader.register_entry_point("test.module.DummyPlugin", DummyPlugin)
        manifest = _make_manifest()
        result = await loader.load(manifest)
        assert isinstance(result, DummyPlugin)

    @pytest.mark.asyncio
    async def test_load_unregistered_raises(self) -> None:
        loader = PluginLoader()
        manifest = _make_manifest(entry_point="unknown.module.Plugin")
        with pytest.raises(PluginLoadError, match="Entry point not found"):
            await loader.load(manifest)

    @pytest.mark.asyncio
    async def test_load_failing_plugin_raises(self) -> None:
        loader = PluginLoader()
        loader.register_entry_point("test.failing.FailingPlugin", FailingPlugin)
        manifest = _make_manifest(entry_point="test.failing.FailingPlugin")
        with pytest.raises(PluginLoadError, match="Instantiation failed"):
            await loader.load(manifest)

    @pytest.mark.asyncio
    async def test_loaded_plugin_is_tracked(self) -> None:
        loader = PluginLoader()
        loader.register_entry_point("test.module.DummyPlugin", DummyPlugin)
        manifest = _make_manifest()
        await loader.load(manifest)
        assert loader.is_loaded("test-plugin")
        assert loader.get_loaded("test-plugin") is not None

    @pytest.mark.asyncio
    async def test_unload_plugin(self) -> None:
        loader = PluginLoader()
        loader.register_entry_point("test.module.DummyPlugin", DummyPlugin)
        manifest = _make_manifest()
        await loader.load(manifest)
        result = await loader.unload("test-plugin")
        assert result is True
        assert not loader.is_loaded("test-plugin")

    @pytest.mark.asyncio
    async def test_unload_not_loaded(self) -> None:
        loader = PluginLoader()
        result = await loader.unload("nonexistent")
        assert result is False


class TestPluginLoaderValidation:
    """Tests for manifest validation."""

    def test_valid_manifest(self) -> None:
        loader = PluginLoader()
        manifest = _make_manifest()
        errors = loader.validate_manifest(manifest)
        assert errors == []

    def test_missing_plugin_id(self) -> None:
        loader = PluginLoader()
        # Need to create with empty values
        m = PluginManifest(
            plugin_id="",
            name="Test",
            version="1.0.0",
            author="Auth",
            description="Desc",
            entry_point="a.b.c",
            permissions=[],
        )
        errors = loader.validate_manifest(m)
        assert "plugin_id is required" in errors

    def test_invalid_version_format(self) -> None:
        loader = PluginLoader()
        m = PluginManifest(
            plugin_id="test",
            name="Test",
            version="bad",
            author="Auth",
            description="Desc",
            entry_point="a.b.c",
            permissions=[],
        )
        errors = loader.validate_manifest(m)
        assert any("semver" in e for e in errors)

    def test_non_numeric_version(self) -> None:
        loader = PluginLoader()
        m = PluginManifest(
            plugin_id="test",
            name="Test",
            version="1.x.0",
            author="Auth",
            description="Desc",
            entry_point="a.b.c",
            permissions=[],
        )
        errors = loader.validate_manifest(m)
        assert any("numeric" in e for e in errors)

    def test_entry_point_no_dot(self) -> None:
        loader = PluginLoader()
        m = PluginManifest(
            plugin_id="test",
            name="Test",
            version="1.0.0",
            author="Auth",
            description="Desc",
            entry_point="nodot",
            permissions=[],
        )
        errors = loader.validate_manifest(m)
        assert any("dotted" in e for e in errors)


class TestPluginLoaderChecksum:
    """Tests for checksum verification."""

    def test_generate_and_verify(self) -> None:
        loader = PluginLoader()
        checksum = loader.generate_checksum("test-plugin")
        assert loader.verify_checksum("test-plugin", checksum) is True

    def test_wrong_checksum(self) -> None:
        loader = PluginLoader()
        loader.generate_checksum("test-plugin")
        assert loader.verify_checksum("test-plugin", "wrong") is False

    def test_set_checksum(self) -> None:
        loader = PluginLoader()
        loader.set_checksum("test-plugin", "abc123")
        assert loader.verify_checksum("test-plugin", "abc123") is True
