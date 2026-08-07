"""Plugin System application layer.

Contains use cases and port (interface) definitions for the Plugin System service.
"""

from sona_plugins.application.ports import (
    PluginPort,
    PluginRegistryPort,
)

__all__ = [
    "PluginPort",
    "PluginRegistryPort",
]
