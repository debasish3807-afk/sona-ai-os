"""Provider metrics collection and reporting."""

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog

logger = structlog.get_logger()


@dataclass
class RequestMetric:
    """A single request metric observation.

    Attributes:
        provider: The provider that served the request.
        model: The model used.
        latency_ms: Request latency in milliseconds.
        tokens_input: Number of input tokens consumed.
        tokens_output: Number of output tokens generated.
        success: Whether the request succeeded.
        error: Error message if the request failed.
        timestamp: When the metric was recorded.
    """

    provider: str
    model: str
    latency_ms: float
    tokens_input: int
    tokens_output: int
    success: bool
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProviderStats:
    """Aggregated statistics for a provider.

    Attributes:
        total_requests: Total number of requests recorded.
        successful: Number of successful requests.
        failed: Number of failed requests.
        avg_latency_ms: Average latency in milliseconds.
        p95_latency_ms: 95th percentile latency.
        p99_latency_ms: 99th percentile latency.
        total_tokens_in: Total input tokens consumed.
        total_tokens_out: Total output tokens generated.
        error_rate: Proportion of requests that failed (0.0 to 1.0).
    """

    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    error_rate: float = 0.0


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Calculate the given percentile from a sorted list.

    Args:
        sorted_values: Pre-sorted list of float values.
        pct: Percentile to compute (0.0 to 1.0).

    Returns:
        The value at the given percentile.
    """
    if not sorted_values:
        return 0.0
    idx = int(len(sorted_values) * pct)
    idx = min(idx, len(sorted_values) - 1)
    return sorted_values[idx]


class ProviderMetrics:
    """Collects and aggregates provider performance metrics.

    Maintains a sliding window of metrics per provider for computing
    real-time performance statistics.
    """

    def __init__(self, window_size: int = 1000) -> None:
        """Initialize provider metrics collector.

        Args:
            window_size: Maximum number of metrics to keep per provider.
        """
        self._metrics: dict[str, deque[RequestMetric]] = {}
        self._window_size = window_size

    def record(self, metric: RequestMetric) -> None:
        """Record a new request metric.

        Args:
            metric: The request metric to record.
        """
        if metric.provider not in self._metrics:
            self._metrics[metric.provider] = deque(maxlen=self._window_size)
        self._metrics[metric.provider].append(metric)
        logger.debug(
            "metric_recorded",
            provider=metric.provider,
            model=metric.model,
            latency_ms=metric.latency_ms,
            success=metric.success,
        )

    def get_stats(self, provider: str) -> ProviderStats:
        """Compute aggregated statistics for a provider.

        Args:
            provider: The provider name to query.

        Returns:
            Aggregated provider statistics.
        """
        metrics = self._metrics.get(provider)
        if not metrics:
            return ProviderStats()

        total = len(metrics)
        successful = sum(1 for m in metrics if m.success)
        failed = total - successful

        latencies = sorted(m.latency_ms for m in metrics if m.success)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return ProviderStats(
            total_requests=total,
            successful=successful,
            failed=failed,
            avg_latency_ms=avg_latency,
            p95_latency_ms=_percentile(latencies, 0.95),
            p99_latency_ms=_percentile(latencies, 0.99),
            total_tokens_in=sum(m.tokens_input for m in metrics),
            total_tokens_out=sum(m.tokens_output for m in metrics),
            error_rate=failed / total if total > 0 else 0.0,
        )

    def get_all_stats(self) -> dict[str, ProviderStats]:
        """Compute aggregated statistics for all providers.

        Returns:
            Dictionary mapping provider names to their statistics.
        """
        return {provider: self.get_stats(provider) for provider in self._metrics}

    def get_error_rate(self, provider: str) -> float:
        """Get the error rate for a specific provider.

        Args:
            provider: The provider name.

        Returns:
            Error rate as a float between 0.0 and 1.0.
        """
        stats = self.get_stats(provider)
        return stats.error_rate

    def get_avg_latency(self, provider: str) -> float:
        """Get the average latency for a specific provider.

        Args:
            provider: The provider name.

        Returns:
            Average latency in milliseconds.
        """
        stats = self.get_stats(provider)
        return stats.avg_latency_ms
