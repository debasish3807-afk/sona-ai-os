"""Pre-defined metrics collector for RAG (Retrieval-Augmented Generation) operations.

Provides standardized metrics for monitoring RAG query performance,
chunk retrieval counts, and confidence scores.
"""

from __future__ import annotations

from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class RAGMetrics:
    """Collects standard RAG operation metrics.

    Metrics:
        - rag_query_total: Counter
        - rag_query_duration_ms: Histogram
        - rag_chunks_retrieved: Histogram
        - rag_confidence: Histogram
    """

    QUERY_TOTAL = "rag_query_total"
    QUERY_DURATION_MS = "rag_query_duration_ms"
    CHUNKS_RETRIEVED = "rag_chunks_retrieved"
    CONFIDENCE = "rag_confidence"

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry

    def record_query(self, duration_ms: float, chunks_retrieved: int, confidence: float) -> None:
        """Record a RAG query operation.

        Args:
            duration_ms: Query duration in milliseconds.
            chunks_retrieved: Number of chunks retrieved.
            confidence: Confidence score (0.0 to 1.0).
        """
        self._registry.increment(self.QUERY_TOTAL)
        self._registry.histogram(self.QUERY_DURATION_MS, duration_ms)
        self._registry.histogram(self.CHUNKS_RETRIEVED, float(chunks_retrieved))
        self._registry.histogram(self.CONFIDENCE, confidence)
