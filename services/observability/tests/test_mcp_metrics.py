"""Unit tests for the MCPMetrics infrastructure module.

Tests cover MCP tool invocation recording, duration tracking,
and error counting with tool labels.
"""

from sona_observability.infrastructure.mcp_metrics import MCPMetrics
from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class TestMCPInvocationRecording:
    """Tests for MCP tool invocation metrics."""

    def test_record_invocation_increments_total(self) -> None:
        """Recording an invocation increments total counter."""
        registry = MetricsRegistry()
        mcp = MCPMetrics(registry)
        mcp.record_invocation("file_read", 50.0)
        assert registry.get_counter("mcp_tool_invocations_total", tags={"tool": "file_read"}) == 1.0

    def test_record_invocation_tracks_duration(self) -> None:
        """Recording an invocation records duration."""
        registry = MetricsRegistry()
        mcp = MCPMetrics(registry)
        mcp.record_invocation("web_search", 200.0)
        values = registry.get_histogram_values("mcp_tool_duration_ms", tags={"tool": "web_search"})
        assert values == [200.0]

    def test_record_invocation_without_error(self) -> None:
        """Normal invocation does not increment error counter."""
        registry = MetricsRegistry()
        mcp = MCPMetrics(registry)
        mcp.record_invocation("file_read", 50.0, error=False)
        assert registry.get_counter("mcp_tool_errors_total", tags={"tool": "file_read"}) == 0.0

    def test_record_invocation_with_error(self) -> None:
        """Error invocation increments both total and error counters."""
        registry = MetricsRegistry()
        mcp = MCPMetrics(registry)
        mcp.record_invocation("database_query", 100.0, error=True)
        assert (
            registry.get_counter("mcp_tool_invocations_total", tags={"tool": "database_query"})
            == 1.0
        )
        assert registry.get_counter("mcp_tool_errors_total", tags={"tool": "database_query"}) == 1.0

    def test_multiple_tools_tracked_separately(self) -> None:
        """Different tools are tracked as separate series."""
        registry = MetricsRegistry()
        mcp = MCPMetrics(registry)
        mcp.record_invocation("file_read", 10.0)
        mcp.record_invocation("file_read", 15.0)
        mcp.record_invocation("web_search", 500.0)
        assert registry.get_counter("mcp_tool_invocations_total", tags={"tool": "file_read"}) == 2.0
        assert (
            registry.get_counter("mcp_tool_invocations_total", tags={"tool": "web_search"}) == 1.0
        )

    def test_error_rate_calculation(self) -> None:
        """Can compute error rate from metrics."""
        registry = MetricsRegistry()
        mcp = MCPMetrics(registry)
        mcp.record_invocation("api_call", 50.0, error=False)
        mcp.record_invocation("api_call", 60.0, error=False)
        mcp.record_invocation("api_call", 70.0, error=True)
        total = registry.get_counter("mcp_tool_invocations_total", tags={"tool": "api_call"})
        errors = registry.get_counter("mcp_tool_errors_total", tags={"tool": "api_call"})
        error_rate = errors / total if total > 0 else 0
        assert abs(error_rate - 1.0 / 3.0) < 0.001
