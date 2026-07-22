"""Plugin & MCP schemas and data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PluginType(str, Enum):
    AI = "ai"
    RESEARCH = "research"
    VISION = "vision"
    VOICE = "voice"
    MEMORY = "memory"
    AUTOMATION = "automation"
    GITHUB = "github"
    TERMINAL = "terminal"
    GENERAL = "general"


class PluginStatus(str, Enum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


class Permission(str, Enum):
    FILESYSTEM_READ = "filesystem:read"
    FILESYSTEM_WRITE = "filesystem:write"
    NETWORK = "network"
    AI_COMPLETE = "ai:complete"
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    TERMINAL = "terminal"
    RESEARCH = "research"
    VISION = "vision"
    VOICE = "voice"


@dataclass
class PluginManifest:
    """Plugin manifest describing metadata and requirements."""

    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    plugin_type: PluginType = PluginType.GENERAL
    permissions: list[Permission] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    entry_point: str = "main.py"
    min_sona_version: str = "1.0.0"
    homepage: str = ""
    license: str = "MIT"


@dataclass
class PluginInfo:
    """Runtime plugin state."""

    manifest: PluginManifest
    status: PluginStatus = PluginStatus.INSTALLED
    installed_at: str = ""
    path: str = ""
    error: str = ""


@dataclass
class MCPTool:
    """MCP tool descriptor."""

    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    provider: str = ""


@dataclass
class MCPResource:
    """MCP resource descriptor."""

    uri: str
    name: str = ""
    description: str = ""
    mime_type: str = ""


@dataclass
class MCPPrompt:
    """MCP prompt template."""

    name: str
    description: str = ""
    arguments: list[dict[str, str]] = field(default_factory=list)
    template: str = ""
