"""Pre-defined metrics collector for memory operations.

Provides standardized metrics for monitoring memory retrieval,
storage, cache hits, and misses across memory types.
"""

from __future__ import annotations

from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class MemoryMetrics:
    """Collects standard memory operation metrics.

    Metrics:
        - memory_retrieval_total: Counter with labels memory_type
        - memory_retrieval_duration_ms: Histogram
        - memory_hit_total: Counter with labels memory_type
        - memory_miss_total: Counter with labels memory_type
        - memory_store_total: Counter with labels memory_type
    """

    RETRIEVAL_TOTAL = "memory_retrieval_total"
    RETRIEVAL_DURATION_MS = "memory_retrieval_duration_ms"
    HIT_TOTAL = "memory_hit_total"
    MISS_TOTAL = "memory_miss_total"
    STORE_TOTAL = "memory_store_total"

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry

    def record_retrieval(self, memory_type: str, duration_ms: float, hit: bool) -> None:
        """Record a memory retrieval operation.

        Args:
            memory_type: Type of memory (e.g., "episodic", "semantic").
            duration_ms: Retrieval duration in milliseconds.
            hit: Whether the retrieval was a hit or miss.
        """
        tags = {"memory_type": memory_type}
        self._registry.increment(self.RETRIEVAL_TOTAL, tags=tags)
        self._registry.histogram(self.RETRIEVAL_DURATION_MS, duration_ms, tags=tags)
        if hit:
            self._registry.increment(self.HIT_TOTAL, tags=tags)
        else:
            self._registry.increment(self.MISS_TOTAL, tags=tags)

    def record_store(self, memory_type: str) -> None:
        """Record a memory store operation.

        Args:
            memory_type: Type of memory being stored.
        """
        tags = {"memory_type": memory_type}
        self._registry.increment(self.STORE_TOTAL, tags=tags)
