"""Plugin System infrastructure layer.

Contains concrete adapter implementations for the Plugin System ports.
Adapters connect to external systems (plugin registries, sandboxes, package managers)
to fulfill the contracts defined in the application layer.
"""

from sona_plugins.infrastructure.builtin_plugins import (
    BUILTIN_MANIFESTS,
    BUILTIN_PLUGINS,
    EchoPlugin,
    FormatterPlugin,
    MetricsPlugin,
    TimerPlugin,
)
from sona_plugins.infrastructure.di import (
    create_plugin_runtime,
    create_plugin_runtime_with_builtins,
)
from sona_plugins.infrastructure.plugin_runtime import PluginRuntime

__all__ = [
    "BUILTIN_MANIFESTS",
    "BUILTIN_PLUGINS",
    "EchoPlugin",
    "FormatterPlugin",
    "MetricsPlugin",
    "PluginRuntime",
    "TimerPlugin",
    "create_plugin_runtime",
    "create_plugin_runtime_with_builtins",
]
