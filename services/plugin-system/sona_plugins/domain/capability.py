"""Plugin capability model."""

from dataclasses import dataclass
from enum import StrEnum


class PluginCapabilityType(StrEnum):
    """Types of capabilities a plugin can provide."""

    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"
    AGENT = "agent"
    MIDDLEWARE = "middleware"
    HOOK = "hook"


@dataclass(frozen=True)
class PluginCapability:
    """Describes a single capability provided by a plugin.

    Attributes:
        name: Human-readable name of the capability.
        capability_type: The type classification of this capability.
        description: Brief description of what this capability does.
        version: Semantic version string for the capability.
    """

    name: str
    capability_type: PluginCapabilityType
    description: str = ""
    version: str = "1.0.0"
