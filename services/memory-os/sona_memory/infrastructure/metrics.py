"""Memory OS metrics tracking.

Tracks operation counts, latencies, memory counts, and hit/miss
ratios for monitoring and observability.
"""

import asyncio
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field


@dataclass
class OperationMetrics:
    """Metrics for a single operation type."""

    count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if self.count == 0:
            return 0.0
        return self.total_latency_ms / self.count


@dataclass
class MemoryMetrics:
    """Aggregated memory system metrics."""

    operations: dict[str, OperationMetrics] = field(default_factory=dict)
    memory_counts: dict[str, dict[str, int]] = field(default_factory=lambda: defaultdict(dict))
    retrieval_hits: int = 0
    retrieval_misses: int = 0

    @property
    def hit_ratio(self) -> float:
        """Ratio of successful retrievals to total retrieval attempts."""
        total = self.retrieval_hits + self.retrieval_misses
        if total == 0:
            return 0.0
        return self.retrieval_hits / total


class MetricsCollector:
    """Collects and reports memory system metrics.

    Thread-safe metrics collection for store, retrieve, consolidate,
    forget operations with latency tracking.
    """

    def __init__(self) -> None:
        self._metrics = MemoryMetrics()
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def track_operation(self, operation: str) -> AsyncIterator[None]:
        """Context manager to track operation latency and count."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            async with self._lock:
                if operation not in self._metrics.operations:
                    self._metrics.operations[operation] = OperationMetrics()
                op = self._metrics.operations[operation]
                op.count += 1
                op.total_latency_ms += elapsed_ms
                op.min_latency_ms = min(op.min_latency_ms, elapsed_ms)
                op.max_latency_ms = max(op.max_latency_ms, elapsed_ms)

    async def record_hit(self) -> None:
        """Record a successful retrieval (results found)."""
        async with self._lock:
            self._metrics.retrieval_hits += 1

    async def record_miss(self) -> None:
        """Record a failed retrieval (no results)."""
        async with self._lock:
            self._metrics.retrieval_misses += 1

    async def update_memory_count(self, user_id: str, memory_type: str, count: int) -> None:
        """Update the current memory count for a user and type."""
        async with self._lock:
            self._metrics.memory_counts[user_id][memory_type] = count

    async def get_metrics(self) -> MemoryMetrics:
        """Get a snapshot of current metrics."""
        async with self._lock:
            return MemoryMetrics(
                operations=dict(self._metrics.operations),
                memory_counts=dict(self._metrics.memory_counts),
                retrieval_hits=self._metrics.retrieval_hits,
                retrieval_misses=self._metrics.retrieval_misses,
            )

    async def reset(self) -> None:
        """Reset all metrics."""
        async with self._lock:
            self._metrics = MemoryMetrics()
