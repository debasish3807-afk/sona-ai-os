"""Plugin permission model."""

from dataclasses import dataclass
from enum import StrEnum


class PluginPermission(StrEnum):
    """Permissions that a plugin can request or be granted."""

    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    NETWORK_HTTP = "network.http"
    NETWORK_WEBSOCKET = "network.websocket"
    DATABASE_READ = "database.read"
    DATABASE_WRITE = "database.write"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    MCP_INVOKE = "mcp.invoke"
    AGENT_EXECUTE = "agent.execute"
    SYSTEM_METRICS = "system.metrics"
    SYSTEM_CONFIG = "system.config"


@dataclass(frozen=True)
class PluginPermissionSet:
    """Represents the required and granted permissions for a plugin.

    Attributes:
        required: The set of permissions the plugin needs.
        granted: The set of permissions the plugin has been granted.
    """

    required: frozenset[PluginPermission]
    granted: frozenset[PluginPermission] = frozenset()

    def is_satisfied(self) -> bool:
        """Check if all required permissions are granted."""
        return self.required.issubset(self.granted)

    def missing(self) -> frozenset[PluginPermission]:
        """Return the set of required permissions that are not yet granted."""
        return self.required - self.granted
