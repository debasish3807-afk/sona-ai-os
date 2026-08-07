"""Unit tests for the MemoryMetrics infrastructure module.

Tests cover memory retrieval, store, hit/miss tracking by memory type.
"""

from sona_observability.infrastructure.memory_metrics import MemoryMetrics
from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class TestMemoryRetrieval:
    """Tests for memory retrieval metrics."""

    def test_record_retrieval_increments_total(self) -> None:
        """Retrieval increments the total counter."""
        registry = MetricsRegistry()
        mm = MemoryMetrics(registry)
        mm.record_retrieval("episodic", 10.0, hit=True)
        assert (
            registry.get_counter("memory_retrieval_total", tags={"memory_type": "episodic"}) == 1.0
        )

    def test_record_retrieval_records_duration(self) -> None:
        """Retrieval records duration in histogram."""
        registry = MetricsRegistry()
        mm = MemoryMetrics(registry)
        mm.record_retrieval("semantic", 25.5, hit=True)
        values = registry.get_histogram_values(
            "memory_retrieval_duration_ms", tags={"memory_type": "semantic"}
        )
        assert values == [25.5]

    def test_record_hit(self) -> None:
        """Hit increments hit counter."""
        registry = MetricsRegistry()
        mm = MemoryMetrics(registry)
        mm.record_retrieval("episodic", 5.0, hit=True)
        assert registry.get_counter("memory_hit_total", tags={"memory_type": "episodic"}) == 1.0
        assert registry.get_counter("memory_miss_total", tags={"memory_type": "episodic"}) == 0.0

    def test_record_miss(self) -> None:
        """Miss increments miss counter."""
        registry = MetricsRegistry()
        mm = MemoryMetrics(registry)
        mm.record_retrieval("semantic", 5.0, hit=False)
        assert registry.get_counter("memory_hit_total", tags={"memory_type": "semantic"}) == 0.0
        assert registry.get_counter("memory_miss_total", tags={"memory_type": "semantic"}) == 1.0

    def test_multiple_retrievals(self) -> None:
        """Multiple retrievals accumulate correctly."""
        registry = MetricsRegistry()
        mm = MemoryMetrics(registry)
        mm.record_retrieval("episodic", 10.0, hit=True)
        mm.record_retrieval("episodic", 15.0, hit=True)
        mm.record_retrieval("episodic", 20.0, hit=False)
        assert (
            registry.get_counter("memory_retrieval_total", tags={"memory_type": "episodic"}) == 3.0
        )
        assert registry.get_counter("memory_hit_total", tags={"memory_type": "episodic"}) == 2.0
        assert registry.get_counter("memory_miss_total", tags={"memory_type": "episodic"}) == 1.0


class TestMemoryStore:
    """Tests for memory store metrics."""

    def test_record_store(self) -> None:
        """Store increments the store counter."""
        registry = MetricsRegistry()
        mm = MemoryMetrics(registry)
        mm.record_store("episodic")
        assert registry.get_counter("memory_store_total", tags={"memory_type": "episodic"}) == 1.0

    def test_multiple_stores(self) -> None:
        """Multiple stores accumulate."""
        registry = MetricsRegistry()
        mm = MemoryMetrics(registry)
        mm.record_store("semantic")
        mm.record_store("semantic")
        mm.record_store("episodic")
        assert registry.get_counter("memory_store_total", tags={"memory_type": "semantic"}) == 2.0
        assert registry.get_counter("memory_store_total", tags={"memory_type": "episodic"}) == 1.0

    def test_different_memory_types(self) -> None:
        """Different memory types tracked separately."""
        registry = MetricsRegistry()
        mm = MemoryMetrics(registry)
        mm.record_store("episodic")
        mm.record_store("semantic")
        mm.record_store("procedural")
        assert registry.get_counter("memory_store_total", tags={"memory_type": "episodic"}) == 1.0
        assert registry.get_counter("memory_store_total", tags={"memory_type": "semantic"}) == 1.0
        assert registry.get_counter("memory_store_total", tags={"memory_type": "procedural"}) == 1.0
