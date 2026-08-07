"""Provider benchmarking for performance comparison."""

import asyncio
import time
from dataclasses import dataclass

import structlog

from sona_ai_kernel.infrastructure.providers.base import CompletionRequest, LLMProviderBase

logger = structlog.get_logger()


@dataclass(frozen=True)
class BenchmarkResult:
    """Results from a provider benchmark run.

    Attributes:
        provider: The provider that was benchmarked.
        model: The model used for benchmarking.
        avg_latency_ms: Average request latency in milliseconds.
        p50_latency_ms: Median latency.
        p95_latency_ms: 95th percentile latency.
        p99_latency_ms: 99th percentile latency.
        throughput_rps: Requests per second achieved.
        error_rate: Proportion of requests that failed.
        total_requests: Total number of requests made.
        total_tokens: Total tokens generated across all requests.
    """

    provider: str
    model: str
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float
    error_rate: float
    total_requests: int
    total_tokens: int


def _percentile_from_sorted(values: list[float], pct: float) -> float:
    """Calculate percentile from a pre-sorted list.

    Args:
        values: Pre-sorted list of values.
        pct: Percentile to compute (0.0 to 1.0).

    Returns:
        The value at the given percentile.
    """
    if not values:
        return 0.0
    idx = int(len(values) * pct)
    idx = min(idx, len(values) - 1)
    return values[idx]


class ProviderBenchmark:
    """Benchmarks providers to establish performance baselines.

    Runs concurrent requests against providers to measure latency,
    throughput, and error rates under load.
    """

    def __init__(self) -> None:
        """Initialize the benchmark runner."""
        self._results: dict[str, BenchmarkResult] = {}

    async def _single_request(
        self, provider: LLMProviderBase, request: CompletionRequest
    ) -> tuple[float, int, bool]:
        """Execute a single benchmark request.

        Args:
            provider: The provider to benchmark.
            request: The completion request to send.

        Returns:
            Tuple of (latency_ms, tokens_output, success).
        """
        start = time.perf_counter()
        try:
            response = await provider.complete(request)
            latency_ms = (time.perf_counter() - start) * 1000.0
            return latency_ms, response.tokens_output, True
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000.0
            logger.debug("benchmark_request_failed", error=str(exc))
            return latency_ms, 0, False

    async def run(
        self,
        provider: LLMProviderBase,
        model: str,
        prompt: str = "Say hello.",
        num_requests: int = 10,
        concurrency: int = 3,
    ) -> BenchmarkResult:
        """Run a benchmark against a provider.

        Sends concurrent requests and measures performance characteristics.

        Args:
            provider: The provider to benchmark.
            model: The model to use.
            prompt: The prompt to send for each request.
            num_requests: Total number of requests to make.
            concurrency: Maximum concurrent requests.

        Returns:
            Benchmark results with latency and throughput metrics.
        """
        request = CompletionRequest(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )

        semaphore = asyncio.Semaphore(concurrency)
        latencies: list[float] = []
        total_tokens = 0
        errors = 0

        async def bounded_request() -> tuple[float, int, bool]:
            async with semaphore:
                return await self._single_request(provider, request)

        start_time = time.perf_counter()
        tasks = [bounded_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time_s = time.perf_counter() - start_time

        for latency_ms, tokens, success in results:
            latencies.append(latency_ms)
            total_tokens += tokens
            if not success:
                errors += 1

        sorted_latencies = sorted(latencies)
        avg_latency = sum(sorted_latencies) / len(sorted_latencies) if sorted_latencies else 0.0

        result = BenchmarkResult(
            provider=provider.name,
            model=model,
            avg_latency_ms=avg_latency,
            p50_latency_ms=_percentile_from_sorted(sorted_latencies, 0.50),
            p95_latency_ms=_percentile_from_sorted(sorted_latencies, 0.95),
            p99_latency_ms=_percentile_from_sorted(sorted_latencies, 0.99),
            throughput_rps=num_requests / total_time_s if total_time_s > 0 else 0.0,
            error_rate=errors / num_requests if num_requests > 0 else 0.0,
            total_requests=num_requests,
            total_tokens=total_tokens,
        )

        self._results[provider.name] = result
        logger.info(
            "benchmark_completed",
            provider=provider.name,
            model=model,
            avg_latency_ms=round(avg_latency, 2),
            throughput_rps=round(result.throughput_rps, 2),
            error_rate=result.error_rate,
        )
        return result

    def get_result(self, provider_name: str) -> BenchmarkResult | None:
        """Get the benchmark result for a specific provider.

        Args:
            provider_name: The provider name to look up.

        Returns:
            The benchmark result, or None if not benchmarked.
        """
        return self._results.get(provider_name)

    def get_fastest(self) -> BenchmarkResult | None:
        """Get the result with the lowest average latency.

        Returns:
            The fastest benchmark result, or None if no results exist.
        """
        if not self._results:
            return None
        return min(self._results.values(), key=lambda r: r.avg_latency_ms)

    def compare(self) -> list[BenchmarkResult]:
        """Get all results sorted by average latency (fastest first).

        Returns:
            List of benchmark results sorted by ascending latency.
        """
        return sorted(self._results.values(), key=lambda r: r.avg_latency_ms)
