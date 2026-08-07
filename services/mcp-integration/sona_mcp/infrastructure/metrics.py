"""MCP metrics tracking for the Integration service.

Tracks invocations, latency, success rates, and per-tool/per-server
statistics for monitoring and observability.
"""

import time
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class ToolStats:
    """Statistics for a single tool.

    Attributes:
        tool_name: Name of the tool.
        total_calls: Total number of invocations.
        successful_calls: Number of successful calls.
        failed_calls: Number of failed calls.
        total_duration_ms: Sum of all call durations.
        min_duration_ms: Minimum call duration.
        max_duration_ms: Maximum call duration.
    """

    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100.0

    @property
    def avg_duration_ms(self) -> float:
        """Calculate the average call duration."""
        if self.total_calls == 0:
            return 0.0
        return self.total_duration_ms / self.total_calls


@dataclass
class ServerStats:
    """Statistics for an MCP server.

    Attributes:
        server_id: Identifier of the server.
        total_calls: Total tool calls to this server.
        successful_calls: Successful calls count.
        failed_calls: Failed calls count.
    """

    server_id: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100.0


@dataclass
class MetricsSnapshot:
    """A point-in-time snapshot of all metrics.

    Attributes:
        total_invocations: Total tool invocations across all tools.
        total_successes: Total successful invocations.
        total_failures: Total failed invocations.
        overall_success_rate: Overall success percentage.
        avg_latency_ms: Average latency across all calls.
        tool_stats: Per-tool statistics.
        server_stats: Per-server statistics.
        timestamp: When this snapshot was taken.
    """

    total_invocations: int = 0
    total_successes: int = 0
    total_failures: int = 0
    overall_success_rate: float = 0.0
    avg_latency_ms: float = 0.0
    tool_stats: dict[str, ToolStats] = field(default_factory=dict)
    server_stats: dict[str, ServerStats] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.monotonic)


class MCPMetrics:
    """Collects and reports MCP runtime metrics.

    Tracks per-tool and per-server statistics including invocation
    counts, latency, and success rates.
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._tool_stats: dict[str, ToolStats] = {}
        self._server_stats: dict[str, ServerStats] = {}
        self._total_invocations = 0
        self._total_successes = 0
        self._total_failures = 0
        self._total_duration_ms = 0.0

    def record_invocation(self, tool_name: str, success: bool, duration_ms: float) -> None:
        """Record a tool invocation result.

        Args:
            tool_name: Name of the tool that was called.
            success: Whether the call succeeded.
            duration_ms: Duration of the call in milliseconds.
        """
        self._total_invocations += 1
        self._total_duration_ms += duration_ms

        if success:
            self._total_successes += 1
        else:
            self._total_failures += 1

        # Update tool stats
        if tool_name not in self._tool_stats:
            self._tool_stats[tool_name] = ToolStats(tool_name=tool_name)

        stats = self._tool_stats[tool_name]
        stats.total_calls += 1
        stats.total_duration_ms += duration_ms
        stats.min_duration_ms = min(stats.min_duration_ms, duration_ms)
        stats.max_duration_ms = max(stats.max_duration_ms, duration_ms)

        if success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1

    def record_server_call(self, server_id: str, success: bool) -> None:
        """Record a call to a specific server.

        Args:
            server_id: The server that received the call.
            success: Whether the call succeeded.
        """
        if server_id not in self._server_stats:
            self._server_stats[server_id] = ServerStats(server_id=server_id)

        stats = self._server_stats[server_id]
        stats.total_calls += 1
        if success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1

    def get_tool_stats(self, tool_name: str) -> ToolStats | None:
        """Get statistics for a specific tool.

        Args:
            tool_name: The tool to get stats for.

        Returns:
            ToolStats if available, None otherwise.
        """
        return self._tool_stats.get(tool_name)

    def get_server_stats(self, server_id: str) -> ServerStats | None:
        """Get statistics for a specific server.

        Args:
            server_id: The server to get stats for.

        Returns:
            ServerStats if available, None otherwise.
        """
        return self._server_stats.get(server_id)

    def get_snapshot(self) -> MetricsSnapshot:
        """Get a point-in-time snapshot of all metrics.

        Returns:
            A MetricsSnapshot with current values.
        """
        avg_latency = 0.0
        if self._total_invocations > 0:
            avg_latency = self._total_duration_ms / self._total_invocations

        success_rate = 0.0
        if self._total_invocations > 0:
            success_rate = (self._total_successes / self._total_invocations) * 100.0

        return MetricsSnapshot(
            total_invocations=self._total_invocations,
            total_successes=self._total_successes,
            total_failures=self._total_failures,
            overall_success_rate=success_rate,
            avg_latency_ms=avg_latency,
            tool_stats=dict(self._tool_stats),
            server_stats=dict(self._server_stats),
        )

    def reset(self) -> None:
        """Reset all metrics."""
        self._tool_stats.clear()
        self._server_stats.clear()
        self._total_invocations = 0
        self._total_successes = 0
        self._total_failures = 0
        self._total_duration_ms = 0.0

    @property
    def total_invocations(self) -> int:
        """Total number of tool invocations."""
        return self._total_invocations

    @property
    def total_successes(self) -> int:
        """Total number of successful invocations."""
        return self._total_successes

    @property
    def total_failures(self) -> int:
        """Total number of failed invocations."""
        return self._total_failures
