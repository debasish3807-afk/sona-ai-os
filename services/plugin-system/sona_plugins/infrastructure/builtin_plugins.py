"""Built-in plugins for testing and demonstration.

Provides functional plugin implementations:
- EchoPlugin: Echoes input back (capability: tool)
- TimerPlugin: Returns timestamps (capability: tool)
- MetricsPlugin: Exposes custom metrics (capability: middleware)
- FormatterPlugin: Formats text (capability: tool)
"""

from __future__ import annotations

from datetime import UTC, datetime

from sona_plugins.application.ports import PluginPort
from sona_plugins.domain.capability import PluginCapability, PluginCapabilityType
from sona_plugins.domain.models import PluginManifest


class EchoPlugin(PluginPort):
    """Echoes input back to the caller.

    A simple tool plugin used for testing the plugin infrastructure.
    """

    MANIFEST = PluginManifest(
        plugin_id="builtin-echo",
        name="Echo Plugin",
        version="1.0.0",
        author="Sona AI OS",
        description="Echoes input back to the caller",
        entry_point="sona_plugins.infrastructure.builtin_plugins.EchoPlugin",
        permissions=[],
    )

    CAPABILITIES = [
        PluginCapability(
            name="echo",
            capability_type=PluginCapabilityType.TOOL,
            description="Echo input text",
        )
    ]

    def __init__(self) -> None:
        self._active = False
        self._invocations: int = 0

    async def activate(self) -> None:
        """Activate the echo plugin."""
        self._active = True

    async def deactivate(self) -> None:
        """Deactivate the echo plugin."""
        self._active = False

    async def get_capabilities(self) -> list[str]:
        """Return echo capability."""
        return ["echo"]

    async def health_check(self) -> bool:
        """Check if plugin is active."""
        return self._active

    async def execute(self, text: str) -> str:
        """Echo the input text."""
        self._invocations += 1
        return text

    @property
    def invocations(self) -> int:
        """Number of times execute has been called."""
        return self._invocations


class TimerPlugin(PluginPort):
    """Returns timestamps and time-related information.

    A tool plugin providing time-related functionality.
    """

    MANIFEST = PluginManifest(
        plugin_id="builtin-timer",
        name="Timer Plugin",
        version="1.0.0",
        author="Sona AI OS",
        description="Provides timestamps and time utilities",
        entry_point="sona_plugins.infrastructure.builtin_plugins.TimerPlugin",
        permissions=[],
    )

    CAPABILITIES = [
        PluginCapability(
            name="timer",
            capability_type=PluginCapabilityType.TOOL,
            description="Get current timestamp",
        )
    ]

    def __init__(self) -> None:
        self._active = False
        self._start_time: datetime | None = None

    async def activate(self) -> None:
        """Activate the timer plugin."""
        self._active = True
        self._start_time = datetime.now(UTC)

    async def deactivate(self) -> None:
        """Deactivate the timer plugin."""
        self._active = False
        self._start_time = None

    async def get_capabilities(self) -> list[str]:
        """Return timer capability."""
        return ["timer"]

    async def health_check(self) -> bool:
        """Check if plugin is active."""
        return self._active

    async def get_timestamp(self) -> str:
        """Get the current UTC timestamp."""
        return datetime.now(UTC).isoformat()

    async def get_uptime_seconds(self) -> float:
        """Get the plugin uptime in seconds."""
        if self._start_time is None:
            return 0.0
        delta = datetime.now(UTC) - self._start_time
        return delta.total_seconds()


class MetricsPlugin(PluginPort):
    """Exposes custom metrics for the plugin system.

    A middleware plugin that tracks and exposes operational metrics.
    """

    MANIFEST = PluginManifest(
        plugin_id="builtin-metrics",
        name="Metrics Plugin",
        version="1.0.0",
        author="Sona AI OS",
        description="Exposes custom metrics for the plugin system",
        entry_point="sona_plugins.infrastructure.builtin_plugins.MetricsPlugin",
        permissions=["system.metrics"],
    )

    CAPABILITIES = [
        PluginCapability(
            name="metrics",
            capability_type=PluginCapabilityType.MIDDLEWARE,
            description="Expose and collect custom metrics",
        )
    ]

    def __init__(self) -> None:
        self._active = False
        self._custom_metrics: dict[str, float] = {}

    async def activate(self) -> None:
        """Activate the metrics plugin."""
        self._active = True

    async def deactivate(self) -> None:
        """Deactivate the metrics plugin."""
        self._active = False

    async def get_capabilities(self) -> list[str]:
        """Return metrics capability."""
        return ["metrics"]

    async def health_check(self) -> bool:
        """Check if plugin is active."""
        return self._active

    async def record_metric(self, name: str, value: float) -> None:
        """Record a custom metric value."""
        self._custom_metrics[name] = value

    async def get_metric(self, name: str) -> float | None:
        """Get a custom metric value."""
        return self._custom_metrics.get(name)

    async def get_all_metrics(self) -> dict[str, float]:
        """Get all recorded metrics."""
        return dict(self._custom_metrics)

    async def reset_metrics(self) -> None:
        """Reset all custom metrics."""
        self._custom_metrics.clear()


class FormatterPlugin(PluginPort):
    """Formats text in various styles.

    A tool plugin providing text formatting capabilities.
    """

    MANIFEST = PluginManifest(
        plugin_id="builtin-formatter",
        name="Formatter Plugin",
        version="1.0.0",
        author="Sona AI OS",
        description="Formats text in various styles",
        entry_point="sona_plugins.infrastructure.builtin_plugins.FormatterPlugin",
        permissions=[],
    )

    CAPABILITIES = [
        PluginCapability(
            name="format",
            capability_type=PluginCapabilityType.TOOL,
            description="Format text in various styles",
        )
    ]

    def __init__(self) -> None:
        self._active = False

    async def activate(self) -> None:
        """Activate the formatter plugin."""
        self._active = True

    async def deactivate(self) -> None:
        """Deactivate the formatter plugin."""
        self._active = False

    async def get_capabilities(self) -> list[str]:
        """Return format capability."""
        return ["format"]

    async def health_check(self) -> bool:
        """Check if plugin is active."""
        return self._active

    async def to_uppercase(self, text: str) -> str:
        """Convert text to uppercase."""
        return text.upper()

    async def to_lowercase(self, text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()

    async def to_title_case(self, text: str) -> str:
        """Convert text to title case."""
        return text.title()

    async def reverse(self, text: str) -> str:
        """Reverse the text."""
        return text[::-1]

    async def word_count(self, text: str) -> int:
        """Count words in text."""
        return len(text.split()) if text.strip() else 0


# Registry of all built-in plugins
BUILTIN_PLUGINS: list[type[PluginPort]] = [
    EchoPlugin,
    TimerPlugin,
    MetricsPlugin,
    FormatterPlugin,
]

BUILTIN_MANIFESTS: list[PluginManifest] = [
    EchoPlugin.MANIFEST,
    TimerPlugin.MANIFEST,
    MetricsPlugin.MANIFEST,
    FormatterPlugin.MANIFEST,
]
