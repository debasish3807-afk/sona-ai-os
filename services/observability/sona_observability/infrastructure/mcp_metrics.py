"""Pre-defined metrics collector for MCP (Model Context Protocol) tool operations.

Provides standardized metrics for monitoring MCP tool invocations,
durations, and errors.
"""

from __future__ import annotations

from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class MCPMetrics:
    """Collects standard MCP tool operation metrics.

    Metrics:
        - mcp_tool_invocations_total: Counter with labels tool
        - mcp_tool_duration_ms: Histogram with labels tool
        - mcp_tool_errors_total: Counter with labels tool
    """

    INVOCATIONS_TOTAL = "mcp_tool_invocations_total"
    DURATION_MS = "mcp_tool_duration_ms"
    ERRORS_TOTAL = "mcp_tool_errors_total"

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry

    def record_invocation(self, tool: str, duration_ms: float, error: bool = False) -> None:
        """Record an MCP tool invocation.

        Args:
            tool: The tool name.
            duration_ms: Invocation duration in milliseconds.
            error: Whether the invocation resulted in an error.
        """
        tags = {"tool": tool}
        self._registry.increment(self.INVOCATIONS_TOTAL, tags=tags)
        self._registry.histogram(self.DURATION_MS, duration_ms, tags=tags)
        if error:
            self._registry.increment(self.ERRORS_TOTAL, tags=tags)
