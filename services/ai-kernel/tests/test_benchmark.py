"""Unit tests for the benchmark module.

Tests verify benchmark run, comparison, and fastest selection.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from sona_ai_kernel.infrastructure.benchmark import (
    BenchmarkResult,
    ProviderBenchmark,
)
from sona_ai_kernel.infrastructure.providers.base import (
    CompletionResponse,
    ProviderConfig,
)


def _make_mock_provider(name: str, latency_ms: float = 50.0, tokens: int = 10):
    """Create a mock provider for benchmark testing."""
    provider = MagicMock()
    provider.name = name
    provider.config = ProviderConfig(name=name, base_url="http://localhost")

    async def mock_complete(request):
        import asyncio

        await asyncio.sleep(latency_ms / 1000.0)
        return CompletionResponse(
            content="hello",
            model="test-model",
            tokens_input=5,
            tokens_output=tokens,
        )

    provider.complete = mock_complete
    return provider


def _make_failing_provider(name: str):
    """Create a mock provider that always fails."""
    provider = MagicMock()
    provider.name = name
    provider.config = ProviderConfig(name=name, base_url="http://localhost")
    provider.complete = AsyncMock(side_effect=RuntimeError("benchmark fail"))
    return provider


class TestBenchmarkResult:
    """Tests for the BenchmarkResult dataclass."""

    def test_frozen(self) -> None:
        """BenchmarkResult is immutable."""
        result = BenchmarkResult(
            provider="test",
            model="model",
            avg_latency_ms=100.0,
            p50_latency_ms=90.0,
            p95_latency_ms=150.0,
            p99_latency_ms=200.0,
            throughput_rps=10.0,
            error_rate=0.0,
            total_requests=10,
            total_tokens=50,
        )
        with pytest.raises(AttributeError):
            result.avg_latency_ms = 0.0  # type: ignore[misc]


class TestProviderBenchmark:
    """Tests for the ProviderBenchmark class."""

    @pytest.mark.asyncio
    async def test_run_returns_result(self) -> None:
        """Benchmark run produces a valid result."""
        benchmark = ProviderBenchmark()
        provider = _make_mock_provider("fast", latency_ms=10.0)

        result = await benchmark.run(
            provider=provider,
            model="test-model",
            num_requests=5,
            concurrency=2,
        )

        assert result.provider == "fast"
        assert result.total_requests == 5
        assert result.avg_latency_ms > 0
        assert result.throughput_rps > 0
        assert result.error_rate == 0.0

    @pytest.mark.asyncio
    async def test_run_records_tokens(self) -> None:
        """Benchmark tracks total tokens generated."""
        benchmark = ProviderBenchmark()
        provider = _make_mock_provider("fast", latency_ms=5.0, tokens=20)

        result = await benchmark.run(
            provider=provider,
            model="test-model",
            num_requests=3,
            concurrency=1,
        )

        assert result.total_tokens == 60  # 3 requests * 20 tokens

    @pytest.mark.asyncio
    async def test_run_handles_failures(self) -> None:
        """Benchmark records error rate when requests fail."""
        benchmark = ProviderBenchmark()
        provider = _make_failing_provider("broken")

        result = await benchmark.run(
            provider=provider,
            model="test-model",
            num_requests=5,
            concurrency=2,
        )

        assert result.error_rate == 1.0
        assert result.total_tokens == 0

    @pytest.mark.asyncio
    async def test_get_result(self) -> None:
        """get_result returns the stored benchmark result."""
        benchmark = ProviderBenchmark()
        provider = _make_mock_provider("openai", latency_ms=5.0)

        await benchmark.run(provider=provider, model="gpt-4o", num_requests=3)

        result = benchmark.get_result("openai")
        assert result is not None
        assert result.provider == "openai"

    def test_get_result_returns_none_for_unknown(self) -> None:
        """get_result returns None for non-benchmarked providers."""
        benchmark = ProviderBenchmark()
        assert benchmark.get_result("unknown") is None

    @pytest.mark.asyncio
    async def test_get_fastest(self) -> None:
        """get_fastest returns the result with lowest avg latency."""
        benchmark = ProviderBenchmark()

        fast_provider = _make_mock_provider("fast", latency_ms=5.0)
        slow_provider = _make_mock_provider("slow", latency_ms=50.0)

        await benchmark.run(fast_provider, "model", num_requests=3)
        await benchmark.run(slow_provider, "model", num_requests=3)

        fastest = benchmark.get_fastest()
        assert fastest is not None
        assert fastest.provider == "fast"

    def test_get_fastest_empty(self) -> None:
        """get_fastest returns None when no results exist."""
        benchmark = ProviderBenchmark()
        assert benchmark.get_fastest() is None

    @pytest.mark.asyncio
    async def test_compare_sorts_by_latency(self) -> None:
        """compare() returns results sorted by ascending latency."""
        benchmark = ProviderBenchmark()

        fast_provider = _make_mock_provider("fast", latency_ms=5.0)
        slow_provider = _make_mock_provider("slow", latency_ms=50.0)

        await benchmark.run(slow_provider, "model", num_requests=3)
        await benchmark.run(fast_provider, "model", num_requests=3)

        results = benchmark.compare()
        assert len(results) == 2
        assert results[0].provider == "fast"
        assert results[1].provider == "slow"

    @pytest.mark.asyncio
    async def test_percentiles_ordered(self) -> None:
        """p50 <= p95 <= p99 in benchmark results."""
        benchmark = ProviderBenchmark()
        provider = _make_mock_provider("test", latency_ms=10.0)

        result = await benchmark.run(provider, "model", num_requests=10, concurrency=2)

        assert result.p50_latency_ms <= result.p95_latency_ms
        assert result.p95_latency_ms <= result.p99_latency_ms
