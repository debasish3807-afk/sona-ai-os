"""Unit tests for Plugin System domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability where expected.
"""

from dataclasses import FrozenInstanceError

import pytest
from sona_plugins.domain.models import (
    PluginInstance,
    PluginManifest,
    PluginStatus,
)


class TestPluginStatus:
    """Tests for the PluginStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all expected plugin statuses are available."""
        assert PluginStatus.ACTIVE == "active"
        assert PluginStatus.INACTIVE == "inactive"
        assert PluginStatus.ERROR == "error"
        assert PluginStatus.LOADING == "loading"

    def test_status_count(self) -> None:
        """Verify exactly 4 plugin statuses exist."""
        assert len(PluginStatus) == 4

    def test_status_is_str_enum(self) -> None:
        """Verify plugin statuses are usable as strings."""
        assert str(PluginStatus.ACTIVE) == "active"
        assert str(PluginStatus.INACTIVE) == "inactive"
        assert str(PluginStatus.ERROR) == "error"
        assert str(PluginStatus.LOADING) == "loading"


class TestPluginManifest:
    """Tests for the PluginManifest frozen dataclass."""

    def test_creation_with_all_fields(self) -> None:
        """Create a manifest with all fields specified."""
        manifest = PluginManifest(
            plugin_id="weather-plugin",
            name="Weather Plugin",
            version="1.0.0",
            author="Sona Labs",
            description="Provides weather information",
            entry_point="plugins.weather.WeatherPlugin",
            permissions=["network", "location"],
            dependencies=["geo-plugin"],
        )
        assert manifest.plugin_id == "weather-plugin"
        assert manifest.name == "Weather Plugin"
        assert manifest.version == "1.0.0"
        assert manifest.author == "Sona Labs"
        assert manifest.description == "Provides weather information"
        assert manifest.entry_point == "plugins.weather.WeatherPlugin"
        assert manifest.permissions == ["network", "location"]
        assert manifest.dependencies == ["geo-plugin"]

    def test_default_dependencies(self) -> None:
        """Verify dependencies defaults to an empty list."""
        manifest = PluginManifest(
            plugin_id="simple-plugin",
            name="Simple Plugin",
            version="0.1.0",
            author="Dev",
            description="A simple plugin",
            entry_point="plugins.simple.SimplePlugin",
            permissions=[],
        )
        assert manifest.dependencies == []

    def test_is_frozen(self) -> None:
        """Verify PluginManifest is immutable."""
        manifest = PluginManifest(
            plugin_id="test-plugin",
            name="Test",
            version="1.0.0",
            author="Test Author",
            description="Test description",
            entry_point="plugins.test.TestPlugin",
            permissions=[],
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            manifest.name = "Changed"  # type: ignore[misc]

    def test_multiple_permissions(self) -> None:
        """Create a manifest with multiple permissions."""
        manifest = PluginManifest(
            plugin_id="full-access-plugin",
            name="Full Access Plugin",
            version="2.0.0",
            author="Admin Corp",
            description="Plugin with many permissions",
            entry_point="plugins.full.FullPlugin",
            permissions=["network", "filesystem", "memory", "kernel"],
            dependencies=["base-plugin", "auth-plugin"],
        )
        assert len(manifest.permissions) == 4
        assert len(manifest.dependencies) == 2


class TestPluginInstance:
    """Tests for the PluginInstance dataclass."""

    def _make_manifest(self) -> PluginManifest:
        """Create a test manifest for use in PluginInstance tests."""
        return PluginManifest(
            plugin_id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            author="Test Author",
            description="A test plugin",
            entry_point="plugins.test.TestPlugin",
            permissions=["network"],
        )

    def test_creation_active(self) -> None:
        """Create an active plugin instance."""
        manifest = self._make_manifest()
        instance = PluginInstance(
            manifest=manifest,
            status=PluginStatus.ACTIVE,
        )
        assert instance.manifest == manifest
        assert instance.status == PluginStatus.ACTIVE
        assert instance.error is None

    def test_creation_with_error(self) -> None:
        """Create a plugin instance in error state."""
        manifest = self._make_manifest()
        instance = PluginInstance(
            manifest=manifest,
            status=PluginStatus.ERROR,
            error="Failed to connect to external API",
        )
        assert instance.status == PluginStatus.ERROR
        assert instance.error == "Failed to connect to external API"

    def test_default_error_is_none(self) -> None:
        """Verify error defaults to None."""
        manifest = self._make_manifest()
        instance = PluginInstance(
            manifest=manifest,
            status=PluginStatus.INACTIVE,
        )
        assert instance.error is None

    def test_is_mutable(self) -> None:
        """Verify PluginInstance status can be updated (not frozen)."""
        manifest = self._make_manifest()
        instance = PluginInstance(
            manifest=manifest,
            status=PluginStatus.LOADING,
        )
        instance.status = PluginStatus.ACTIVE
        assert instance.status == PluginStatus.ACTIVE

    def test_transition_to_error(self) -> None:
        """Verify a plugin instance can transition to error state."""
        manifest = self._make_manifest()
        instance = PluginInstance(
            manifest=manifest,
            status=PluginStatus.ACTIVE,
        )
        instance.status = PluginStatus.ERROR
        instance.error = "Unhandled exception in plugin"
        assert instance.status == PluginStatus.ERROR
        assert instance.error == "Unhandled exception in plugin"

    def test_all_statuses_assignable(self) -> None:
        """Verify all PluginStatus values can be assigned to an instance."""
        manifest = self._make_manifest()
        instance = PluginInstance(manifest=manifest, status=PluginStatus.INACTIVE)

        for status in PluginStatus:
            instance.status = status
            assert instance.status == status
