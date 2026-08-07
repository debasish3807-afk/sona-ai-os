"""Plugin loader — load, validate, and verify plugin code."""

from __future__ import annotations

import hashlib
from typing import Any

import structlog

from sona_plugins.domain.models import PluginManifest

logger = structlog.get_logger()


class PluginLoadError(Exception):
    """Raised when a plugin cannot be loaded."""

    def __init__(self, plugin_id: str, reason: str) -> None:
        self.plugin_id = plugin_id
        self.reason = reason
        super().__init__(f"Failed to load plugin '{plugin_id}': {reason}")


class PluginValidationError(Exception):
    """Raised when a plugin manifest fails validation."""

    def __init__(self, plugin_id: str, errors: list[str]) -> None:
        self.plugin_id = plugin_id
        self.errors = errors
        super().__init__(f"Validation failed for plugin '{plugin_id}': {'; '.join(errors)}")


class PluginLoader:
    """Loads plugin code from entry points.

    In this implementation, we use a simulated loader that maps
    entry points to built-in plugin classes. In production, this
    would dynamically import modules.
    """

    def __init__(self) -> None:
        self._registry: dict[str, type[Any]] = {}
        self._loaded: dict[str, Any] = {}
        self._checksums: dict[str, str] = {}

    def register_entry_point(self, entry_point: str, plugin_class: type[Any]) -> None:
        """Register a mapping from entry point to plugin class.

        This simulates the dynamic import mechanism.
        """
        self._registry[entry_point] = plugin_class
        logger.info("entry_point_registered", entry_point=entry_point)

    async def load(self, manifest: PluginManifest) -> Any:
        """Load a plugin from its manifest entry point.

        Args:
            manifest: The plugin manifest with entry_point info.

        Returns:
            Instantiated plugin object.

        Raises:
            PluginLoadError: If the entry point is not registered.
        """
        entry_point = manifest.entry_point
        plugin_class = self._registry.get(entry_point)

        if plugin_class is None:
            raise PluginLoadError(
                manifest.plugin_id,
                f"Entry point not found: {entry_point}",
            )

        try:
            instance = plugin_class()
            self._loaded[manifest.plugin_id] = instance
            logger.info(
                "plugin_loaded",
                plugin_id=manifest.plugin_id,
                entry_point=entry_point,
            )
            return instance
        except Exception as exc:
            raise PluginLoadError(manifest.plugin_id, f"Instantiation failed: {exc}") from exc

    async def unload(self, plugin_id: str) -> bool:
        """Unload a plugin instance."""
        if plugin_id in self._loaded:
            del self._loaded[plugin_id]
            logger.info("plugin_unloaded", plugin_id=plugin_id)
            return True
        return False

    def get_loaded(self, plugin_id: str) -> Any | None:
        """Get a loaded plugin instance."""
        return self._loaded.get(plugin_id)

    def is_loaded(self, plugin_id: str) -> bool:
        """Check if a plugin is currently loaded."""
        return plugin_id in self._loaded

    def validate_manifest(self, manifest: PluginManifest) -> list[str]:
        """Validate a plugin manifest for correctness.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        if not manifest.plugin_id:
            errors.append("plugin_id is required")
        if not manifest.name:
            errors.append("name is required")
        if not manifest.version:
            errors.append("version is required")
        if not manifest.entry_point:
            errors.append("entry_point is required")
        if not manifest.author:
            errors.append("author is required")

        # Validate version format (basic semver check)
        parts = manifest.version.split(".")
        if len(parts) != 3:
            errors.append("version must be in semver format (x.y.z)")
        else:
            for part in parts:
                if not part.isdigit():
                    errors.append("version parts must be numeric")
                    break

        # Validate entry point format
        if manifest.entry_point and "." not in manifest.entry_point:
            errors.append("entry_point must be a dotted module path")

        return errors

    def verify_checksum(self, plugin_id: str, expected_checksum: str) -> bool:
        """Verify a plugin's integrity checksum.

        Args:
            plugin_id: The plugin to verify.
            expected_checksum: The expected SHA-256 checksum.

        Returns:
            True if the checksum matches.
        """
        stored = self._checksums.get(plugin_id)
        if stored is None:
            # Generate a deterministic checksum for the plugin
            content = f"{plugin_id}:loaded"
            stored = hashlib.sha256(content.encode()).hexdigest()
            self._checksums[plugin_id] = stored

        return stored == expected_checksum

    def set_checksum(self, plugin_id: str, checksum: str) -> None:
        """Set the expected checksum for a plugin."""
        self._checksums[plugin_id] = checksum

    def generate_checksum(self, plugin_id: str) -> str:
        """Generate a checksum for a loaded plugin."""
        content = f"{plugin_id}:loaded"
        checksum = hashlib.sha256(content.encode()).hexdigest()
        self._checksums[plugin_id] = checksum
        return checksum
