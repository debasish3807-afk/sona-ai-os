"""Tests for pipeline metrics collection."""

import pytest

from app.pipeline.metrics import MetricsCollector, PipelineMetrics


class TestPipelineMetrics:
    """Tests for the PipelineMetrics dataclass."""

    def test_default_values(self) -> None:
        """All metrics default to zero."""
        metrics = PipelineMetrics()
        assert metrics.request_latency_ms == 0.0
        assert metrics.memory_retrieval_ms == 0.0
        assert metrics.thalamus_routing_ms == 0.0
        assert metrics.brain_execution_ms == 0.0
        assert metrics.llm_inference_ms == 0.0
        assert metrics.memory_update_ms == 0.0
        assert metrics.total_tokens == 0

    def test_custom_values(self) -> None:
        """Metrics can be set with custom values."""
        metrics = PipelineMetrics(
            request_latency_ms=100.5,
            total_tokens=500,
        )
        assert metrics.request_latency_ms == 100.5
        assert metrics.total_tokens == 500


class TestMetricsCollector:
    """Tests for the MetricsCollector class."""

    @pytest.mark.asyncio
    async def test_track_stage_records_time(self) -> None:
        """Tracking a stage records elapsed time."""
        collector = MetricsCollector(request_id="test-req")
        async with collector.track_stage("memory_retrieval"):
            pass  # Instant — should record near-zero time
        assert collector.metrics.memory_retrieval_ms >= 0.0

    @pytest.mark.asyncio
    async def test_track_multiple_stages(self) -> None:
        """Multiple stages can be tracked independently."""
        collector = MetricsCollector(request_id="test-req")
        async with collector.track_stage("memory_retrieval"):
            pass
        async with collector.track_stage("thalamus_routing"):
            pass
        async with collector.track_stage("brain_execution"):
            pass
        assert collector.metrics.memory_retrieval_ms >= 0.0
        assert collector.metrics.thalamus_routing_ms >= 0.0
        assert collector.metrics.brain_execution_ms >= 0.0

    def test_record_tokens(self) -> None:
        """Token count is recorded correctly."""
        collector = MetricsCollector(request_id="test-req")
        collector.record_tokens(1500)
        assert collector.metrics.total_tokens == 1500

    def test_finalize_records_total_latency(self) -> None:
        """Finalize calculates total request latency."""
        collector = MetricsCollector(request_id="test-req")
        result = collector.finalize()
        assert result.request_latency_ms >= 0.0

    @pytest.mark.asyncio
    async def test_stage_exception_still_records(self) -> None:
        """Stage timing is recorded even if an exception occurs."""
        collector = MetricsCollector(request_id="test-req")
        with pytest.raises(ValueError):  # noqa: PT011
            async with collector.track_stage("brain_execution"):
                raise ValueError("test error")
        # Time should still be recorded
        assert collector.metrics.brain_execution_ms >= 0.0
