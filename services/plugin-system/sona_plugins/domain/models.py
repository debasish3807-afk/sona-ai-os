"""Domain models for the Plugin System service.

Defines the data structures used by the Plugin System for plugin lifecycle
management, registration, and capability discovery.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class PluginStatus(StrEnum):
    """Plugin lifecycle status.

    Tracks the current state of a plugin instance within the system.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"


@dataclass(frozen=True)
class PluginManifest:
    """Declarative metadata describing a plugin.

    Contains all information needed to install, validate, and activate
    a plugin within the Sona AI OS platform.

    Attributes:
        plugin_id: Unique identifier for the plugin.
        name: Human-readable plugin name.
        version: Semantic version string (e.g., "1.2.3").
        author: Plugin author or organization name.
        description: Brief description of plugin functionality.
        entry_point: Module path to the plugin's main class.
        permissions: List of permissions the plugin requires.
        dependencies: List of other plugin IDs this plugin depends on.
    """

    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    permissions: list[str]
    dependencies: list[str] = field(default_factory=list)


@dataclass
class PluginInstance:
    """A running plugin instance with its current state.

    Represents a plugin that has been installed in the system,
    tracking its manifest metadata and current lifecycle status.

    Attributes:
        manifest: The plugin's declarative manifest metadata.
        status: Current lifecycle status of the plugin.
        error: Error message if the plugin is in ERROR status, None otherwise.
    """

    manifest: PluginManifest
    status: PluginStatus
    error: str | None = None
