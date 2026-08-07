"""Unit tests for the provider metrics module.

Tests verify recording, stats calculation, percentiles, and error rate.
"""

import pytest

from sona_ai_kernel.infrastructure.metrics import (
    ProviderMetrics,
    RequestMetric,
    _percentile,
)


class TestPercentile:
    """Tests for the _percentile helper function."""

    def test_empty_list(self) -> None:
        """Returns 0 for empty list."""
        assert _percentile([], 0.95) == 0.0

    def test_single_value(self) -> None:
        """Returns the single value for any percentile."""
        assert _percentile([5.0], 0.99) == 5.0

    def test_p50_median(self) -> None:
        """Returns approximate median for sorted list."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _percentile(values, 0.50)
        assert result == 3.0

    def test_p95(self) -> None:
        """Returns approximate 95th percentile."""
        values = list(range(1, 101))  # 1 to 100
        values_float = [float(v) for v in values]
        result = _percentile(values_float, 0.95)
        assert result >= 95.0


class TestProviderMetrics:
    """Tests for the ProviderMetrics class."""

    def test_record_metric(self) -> None:
        """Recording a metric adds it to the provider's collection."""
        metrics = ProviderMetrics()
        metric = RequestMetric(
            provider="openai",
            model="gpt-4o",
            latency_ms=100.0,
            tokens_input=10,
            tokens_output=5,
            success=True,
        )
        metrics.record(metric)

        stats = metrics.get_stats("openai")
        assert stats.total_requests == 1
        assert stats.successful == 1

    def test_empty_provider_stats(self) -> None:
        """get_stats returns empty stats for unknown provider."""
        metrics = ProviderMetrics()
        stats = metrics.get_stats("unknown")
        assert stats.total_requests == 0
        assert stats.avg_latency_ms == 0.0

    def test_avg_latency_calculation(self) -> None:
        """Average latency calculated from successful requests only."""
        metrics = ProviderMetrics()

        for latency in [100.0, 200.0, 300.0]:
            metrics.record(
                RequestMetric(
                    provider="openai",
                    model="gpt-4o",
                    latency_ms=latency,
                    tokens_input=10,
                    tokens_output=5,
                    success=True,
                )
            )

        stats = metrics.get_stats("openai")
        assert stats.avg_latency_ms == pytest.approx(200.0)

    def test_error_rate_calculation(self) -> None:
        """Error rate is failures / total requests."""
        metrics = ProviderMetrics()

        # 3 successes, 2 failures
        for i in range(5):
            metrics.record(
                RequestMetric(
                    provider="openai",
                    model="gpt-4o",
                    latency_ms=100.0,
                    tokens_input=10,
                    tokens_output=5,
                    success=i < 3,
                    error="fail" if i >= 3 else None,
                )
            )

        stats = metrics.get_stats("openai")
        assert stats.error_rate == pytest.approx(0.4)

    def test_token_totals(self) -> None:
        """Total tokens are summed across all requests."""
        metrics = ProviderMetrics()

        for _ in range(3):
            metrics.record(
                RequestMetric(
                    provider="openai",
                    model="gpt-4o",
                    latency_ms=100.0,
                    tokens_input=100,
                    tokens_output=50,
                    success=True,
                )
            )

        stats = metrics.get_stats("openai")
        assert stats.total_tokens_in == 300
        assert stats.total_tokens_out == 150

    def test_get_all_stats(self) -> None:
        """get_all_stats returns stats for all recorded providers."""
        metrics = ProviderMetrics()

        metrics.record(
            RequestMetric(
                provider="openai",
                model="gpt-4o",
                latency_ms=100.0,
                tokens_input=10,
                tokens_output=5,
                success=True,
            )
        )
        metrics.record(
            RequestMetric(
                provider="anthropic",
                model="claude",
                latency_ms=200.0,
                tokens_input=20,
                tokens_output=10,
                success=True,
            )
        )

        all_stats = metrics.get_all_stats()
        assert "openai" in all_stats
        assert "anthropic" in all_stats

    def test_get_error_rate_convenience(self) -> None:
        """get_error_rate returns the error rate directly."""
        metrics = ProviderMetrics()
        metrics.record(
            RequestMetric(
                provider="openai",
                model="gpt-4o",
                latency_ms=100.0,
                tokens_input=10,
                tokens_output=5,
                success=False,
                error="err",
            )
        )
        assert metrics.get_error_rate("openai") == 1.0

    def test_get_avg_latency_convenience(self) -> None:
        """get_avg_latency returns average latency directly."""
        metrics = ProviderMetrics()
        metrics.record(
            RequestMetric(
                provider="openai",
                model="gpt-4o",
                latency_ms=150.0,
                tokens_input=10,
                tokens_output=5,
                success=True,
            )
        )
        assert metrics.get_avg_latency("openai") == 150.0

    def test_window_size_limits_metrics(self) -> None:
        """Metrics beyond window_size are discarded (FIFO)."""
        metrics = ProviderMetrics(window_size=3)

        for i in range(5):
            metrics.record(
                RequestMetric(
                    provider="openai",
                    model="gpt-4o",
                    latency_ms=float(i * 100),
                    tokens_input=10,
                    tokens_output=5,
                    success=True,
                )
            )

        stats = metrics.get_stats("openai")
        assert stats.total_requests == 3  # Only last 3 retained

    def test_percentile_stats(self) -> None:
        """p95 and p99 are correctly computed from latencies."""
        metrics = ProviderMetrics()

        for i in range(100):
            metrics.record(
                RequestMetric(
                    provider="openai",
                    model="gpt-4o",
                    latency_ms=float(i + 1),
                    tokens_input=10,
                    tokens_output=5,
                    success=True,
                )
            )

        stats = metrics.get_stats("openai")
        assert stats.p95_latency_ms >= 95.0
        assert stats.p99_latency_ms >= 99.0
