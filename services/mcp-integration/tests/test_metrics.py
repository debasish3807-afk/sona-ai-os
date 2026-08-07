"""Unit tests for MCPMetrics."""

from sona_mcp.infrastructure.metrics import MCPMetrics, ToolStats


class TestMCPMetricsRecording:
    def test_record_successful_invocation(self) -> None:
        metrics = MCPMetrics()
        metrics.record_invocation("tool1", True, 50.0)
        assert metrics.total_invocations == 1
        assert metrics.total_successes == 1
        assert metrics.total_failures == 0

    def test_record_failed_invocation(self) -> None:
        metrics = MCPMetrics()
        metrics.record_invocation("tool1", False, 10.0)
        assert metrics.total_invocations == 1
        assert metrics.total_successes == 0
        assert metrics.total_failures == 1

    def test_multiple_invocations(self) -> None:
        metrics = MCPMetrics()
        metrics.record_invocation("t1", True, 10.0)
        metrics.record_invocation("t1", True, 20.0)
        metrics.record_invocation("t1", False, 5.0)
        assert metrics.total_invocations == 3
        assert metrics.total_successes == 2
        assert metrics.total_failures == 1

    def test_record_server_call(self) -> None:
        metrics = MCPMetrics()
        metrics.record_server_call("srv-1", True)
        metrics.record_server_call("srv-1", False)
        stats = metrics.get_server_stats("srv-1")
        assert stats is not None
        assert stats.total_calls == 2
        assert stats.successful_calls == 1
        assert stats.failed_calls == 1


class TestMCPMetricsToolStats:
    def test_get_tool_stats(self) -> None:
        metrics = MCPMetrics()
        metrics.record_invocation("tool1", True, 50.0)
        metrics.record_invocation("tool1", True, 100.0)
        stats = metrics.get_tool_stats("tool1")
        assert stats is not None
        assert stats.total_calls == 2
        assert stats.successful_calls == 2

    def test_tool_stats_min_max_duration(self) -> None:
        metrics = MCPMetrics()
        metrics.record_invocation("tool1", True, 10.0)
        metrics.record_invocation("tool1", True, 50.0)
        metrics.record_invocation("tool1", True, 30.0)
        stats = metrics.get_tool_stats("tool1")
        assert stats is not None
        assert stats.min_duration_ms == 10.0
        assert stats.max_duration_ms == 50.0

    def test_tool_stats_missing(self) -> None:
        metrics = MCPMetrics()
        assert metrics.get_tool_stats("missing") is None

    def test_tool_stats_success_rate(self) -> None:
        stats = ToolStats(
            tool_name="t1",
            total_calls=10,
            successful_calls=8,
            failed_calls=2,
        )
        assert stats.success_rate == 80.0

    def test_tool_stats_avg_duration(self) -> None:
        stats = ToolStats(
            tool_name="t1",
            total_calls=4,
            total_duration_ms=100.0,
        )
        assert stats.avg_duration_ms == 25.0

    def test_tool_stats_zero_calls(self) -> None:
        stats = ToolStats(tool_name="t1")
        assert stats.success_rate == 0.0
        assert stats.avg_duration_ms == 0.0


class TestMCPMetricsSnapshot:
    def test_get_snapshot_empty(self) -> None:
        metrics = MCPMetrics()
        snap = metrics.get_snapshot()
        assert snap.total_invocations == 0
        assert snap.overall_success_rate == 0.0
        assert snap.avg_latency_ms == 0.0

    def test_get_snapshot_with_data(self) -> None:
        metrics = MCPMetrics()
        metrics.record_invocation("t1", True, 20.0)
        metrics.record_invocation("t2", False, 10.0)
        snap = metrics.get_snapshot()
        assert snap.total_invocations == 2
        assert snap.total_successes == 1
        assert snap.total_failures == 1
        assert snap.overall_success_rate == 50.0
        assert snap.avg_latency_ms == 15.0

    def test_snapshot_includes_tool_stats(self) -> None:
        metrics = MCPMetrics()
        metrics.record_invocation("tool_a", True, 10.0)
        snap = metrics.get_snapshot()
        assert "tool_a" in snap.tool_stats

    def test_snapshot_includes_server_stats(self) -> None:
        metrics = MCPMetrics()
        metrics.record_server_call("srv-1", True)
        snap = metrics.get_snapshot()
        assert "srv-1" in snap.server_stats


class TestMCPMetricsReset:
    def test_reset_clears_all(self) -> None:
        metrics = MCPMetrics()
        metrics.record_invocation("t1", True, 10.0)
        metrics.record_server_call("s1", True)
        metrics.reset()
        assert metrics.total_invocations == 0
        assert metrics.total_successes == 0
        assert metrics.total_failures == 0
        assert metrics.get_tool_stats("t1") is None
        assert metrics.get_server_stats("s1") is None
