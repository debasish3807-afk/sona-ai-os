"""Unit tests for the RAGMetrics infrastructure module.

Tests cover RAG query recording, duration tracking, chunk count,
and confidence score histograms.
"""

from sona_observability.infrastructure.metrics_registry import MetricsRegistry
from sona_observability.infrastructure.rag_metrics import RAGMetrics


class TestRAGQueryRecording:
    """Tests for RAG query metric recording."""

    def test_record_query_increments_total(self) -> None:
        """Recording a query increments total counter."""
        registry = MetricsRegistry()
        rag = RAGMetrics(registry)
        rag.record_query(100.0, 5, 0.85)
        assert registry.get_counter("rag_query_total") == 1.0

    def test_record_query_tracks_duration(self) -> None:
        """Recording a query records duration."""
        registry = MetricsRegistry()
        rag = RAGMetrics(registry)
        rag.record_query(150.5, 3, 0.9)
        values = registry.get_histogram_values("rag_query_duration_ms")
        assert values == [150.5]

    def test_record_query_tracks_chunks(self) -> None:
        """Recording a query records chunk count."""
        registry = MetricsRegistry()
        rag = RAGMetrics(registry)
        rag.record_query(100.0, 7, 0.8)
        values = registry.get_histogram_values("rag_chunks_retrieved")
        assert values == [7.0]

    def test_record_query_tracks_confidence(self) -> None:
        """Recording a query records confidence score."""
        registry = MetricsRegistry()
        rag = RAGMetrics(registry)
        rag.record_query(100.0, 5, 0.92)
        values = registry.get_histogram_values("rag_confidence")
        assert values == [0.92]

    def test_multiple_queries(self) -> None:
        """Multiple queries accumulate correctly."""
        registry = MetricsRegistry()
        rag = RAGMetrics(registry)
        rag.record_query(100.0, 3, 0.8)
        rag.record_query(200.0, 5, 0.9)
        rag.record_query(150.0, 4, 0.85)
        assert registry.get_counter("rag_query_total") == 3.0
        durations = registry.get_histogram_values("rag_query_duration_ms")
        assert durations == [100.0, 200.0, 150.0]

    def test_confidence_range(self) -> None:
        """Confidence values are stored as-is."""
        registry = MetricsRegistry()
        rag = RAGMetrics(registry)
        rag.record_query(50.0, 1, 0.0)
        rag.record_query(50.0, 1, 1.0)
        values = registry.get_histogram_values("rag_confidence")
        assert values == [0.0, 1.0]

    def test_zero_chunks(self) -> None:
        """Zero chunks retrieved is valid."""
        registry = MetricsRegistry()
        rag = RAGMetrics(registry)
        rag.record_query(50.0, 0, 0.1)
        values = registry.get_histogram_values("rag_chunks_retrieved")
        assert values == [0.0]
