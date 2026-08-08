"""Domain events for the Plugin System."""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class PluginInstalledEvent(DomainEvent):
    """Emitted when a plugin is successfully installed."""

    plugin_id: str = ""
    name: str = ""
    version: str = ""


@dataclass(frozen=True)
class PluginActivatedEvent(DomainEvent):
    """Emitted when a plugin is activated and enters running state."""

    plugin_id: str = ""


@dataclass(frozen=True)
class PluginDeactivatedEvent(DomainEvent):
    """Emitted when a plugin is deactivated."""

    plugin_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class PluginFailedEvent(DomainEvent):
    """Emitted when a plugin encounters an error."""

    plugin_id: str = ""
    error: str = ""
    state: str = ""


@dataclass(frozen=True)
class PluginExecutedEvent(DomainEvent):
    """Emitted when a plugin action is executed."""

    plugin_id: str = ""
    action: str = ""
    duration_ms: float = 0.0
    success: bool = True
