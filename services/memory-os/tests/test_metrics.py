"""Unit tests for memory metrics tracking."""

import asyncio

import pytest

from sona_memory.infrastructure.metrics import MetricsCollector, OperationMetrics


class TestOperationMetrics:
    """Tests for the OperationMetrics data class."""

    def test_defaults(self) -> None:
        m = OperationMetrics()
        assert m.count == 0
        assert m.total_latency_ms == 0.0
        assert m.avg_latency_ms == 0.0

    def test_avg_latency(self) -> None:
        m = OperationMetrics(count=4, total_latency_ms=100.0)
        assert m.avg_latency_ms == 25.0

    def test_avg_latency_zero_count(self) -> None:
        m = OperationMetrics(count=0, total_latency_ms=0.0)
        assert m.avg_latency_ms == 0.0


class TestMetricsCollector:
    """Tests for the MetricsCollector."""

    @pytest.mark.asyncio
    async def test_track_operation(self) -> None:
        mc = MetricsCollector()
        async with mc.track_operation("store"):
            await asyncio.sleep(0.01)
        metrics = await mc.get_metrics()
        assert "store" in metrics.operations
        assert metrics.operations["store"].count == 1
        assert metrics.operations["store"].total_latency_ms > 0

    @pytest.mark.asyncio
    async def test_track_multiple_operations(self) -> None:
        mc = MetricsCollector()
        async with mc.track_operation("store"):
            pass
        async with mc.track_operation("store"):
            pass
        async with mc.track_operation("retrieve"):
            pass
        metrics = await mc.get_metrics()
        assert metrics.operations["store"].count == 2
        assert metrics.operations["retrieve"].count == 1

    @pytest.mark.asyncio
    async def test_min_max_latency(self) -> None:
        mc = MetricsCollector()
        async with mc.track_operation("op"):
            await asyncio.sleep(0.01)
        async with mc.track_operation("op"):
            await asyncio.sleep(0.02)
        metrics = await mc.get_metrics()
        op = metrics.operations["op"]
        assert op.min_latency_ms <= op.max_latency_ms

    @pytest.mark.asyncio
    async def test_record_hit(self) -> None:
        mc = MetricsCollector()
        await mc.record_hit()
        await mc.record_hit()
        metrics = await mc.get_metrics()
        assert metrics.retrieval_hits == 2

    @pytest.mark.asyncio
    async def test_record_miss(self) -> None:
        mc = MetricsCollector()
        await mc.record_miss()
        metrics = await mc.get_metrics()
        assert metrics.retrieval_misses == 1

    @pytest.mark.asyncio
    async def test_hit_ratio(self) -> None:
        mc = MetricsCollector()
        await mc.record_hit()
        await mc.record_hit()
        await mc.record_miss()
        metrics = await mc.get_metrics()
        assert abs(metrics.hit_ratio - 2 / 3) < 0.01

    @pytest.mark.asyncio
    async def test_hit_ratio_zero(self) -> None:
        mc = MetricsCollector()
        metrics = await mc.get_metrics()
        assert metrics.hit_ratio == 0.0

    @pytest.mark.asyncio
    async def test_update_memory_count(self) -> None:
        mc = MetricsCollector()
        await mc.update_memory_count("user1", "working", 5)
        metrics = await mc.get_metrics()
        assert metrics.memory_counts["user1"]["working"] == 5

    @pytest.mark.asyncio
    async def test_reset(self) -> None:
        mc = MetricsCollector()
        await mc.record_hit()
        async with mc.track_operation("op"):
            pass
        await mc.reset()
        metrics = await mc.get_metrics()
        assert metrics.retrieval_hits == 0
        assert len(metrics.operations) == 0

    @pytest.mark.asyncio
    async def test_operation_exception_still_records(self) -> None:
        mc = MetricsCollector()
        with pytest.raises(ValueError):
            async with mc.track_operation("failing"):
                raise ValueError("oops")
        metrics = await mc.get_metrics()
        assert metrics.operations["failing"].count == 1

    @pytest.mark.asyncio
    async def test_concurrent_tracking(self) -> None:
        mc = MetricsCollector()

        async def do_op() -> None:
            async with mc.track_operation("concurrent"):
                await asyncio.sleep(0.01)

        await asyncio.gather(*[do_op() for _ in range(10)])
        metrics = await mc.get_metrics()
        assert metrics.operations["concurrent"].count == 10
