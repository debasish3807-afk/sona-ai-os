"""Plugin lifecycle state machine."""

from enum import StrEnum


class PluginLifecycleState(StrEnum):
    """States in the plugin lifecycle state machine."""

    DISCOVERED = "discovered"
    INSTALLED = "installed"
    VERIFIED = "verified"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    STARTED = "started"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"
    REMOVED = "removed"
    ERROR = "error"


VALID_TRANSITIONS: dict[PluginLifecycleState, list[PluginLifecycleState]] = {
    PluginLifecycleState.DISCOVERED: [
        PluginLifecycleState.INSTALLED,
        PluginLifecycleState.REMOVED,
    ],
    PluginLifecycleState.INSTALLED: [
        PluginLifecycleState.VERIFIED,
        PluginLifecycleState.REMOVED,
        PluginLifecycleState.ERROR,
    ],
    PluginLifecycleState.VERIFIED: [
        PluginLifecycleState.LOADED,
        PluginLifecycleState.REMOVED,
    ],
    PluginLifecycleState.LOADED: [
        PluginLifecycleState.INITIALIZED,
        PluginLifecycleState.UNLOADING,
        PluginLifecycleState.ERROR,
    ],
    PluginLifecycleState.INITIALIZED: [
        PluginLifecycleState.STARTED,
        PluginLifecycleState.UNLOADING,
        PluginLifecycleState.ERROR,
    ],
    PluginLifecycleState.STARTED: [
        PluginLifecycleState.RUNNING,
        PluginLifecycleState.ERROR,
    ],
    PluginLifecycleState.RUNNING: [
        PluginLifecycleState.STOPPING,
        PluginLifecycleState.ERROR,
    ],
    PluginLifecycleState.STOPPING: [
        PluginLifecycleState.STOPPED,
    ],
    PluginLifecycleState.STOPPED: [
        PluginLifecycleState.STARTED,
        PluginLifecycleState.UNLOADING,
        PluginLifecycleState.REMOVED,
    ],
    PluginLifecycleState.UNLOADING: [
        PluginLifecycleState.UNLOADED,
    ],
    PluginLifecycleState.UNLOADED: [
        PluginLifecycleState.LOADED,
        PluginLifecycleState.REMOVED,
    ],
    PluginLifecycleState.REMOVED: [],
    PluginLifecycleState.ERROR: [
        PluginLifecycleState.STOPPED,
        PluginLifecycleState.REMOVED,
    ],
}
