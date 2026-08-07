"""Observability runtime orchestrator.

Combines metrics, tracing, and logging into a unified API that provides
a single entry point for all observability operations.
"""

from __future__ import annotations

from typing import Any

from sona_observability.domain.models import LogLevel, SpanContext
from sona_observability.infrastructure.correlation import CorrelationManager
from sona_observability.infrastructure.health_reporter import HealthReporter
from sona_observability.infrastructure.llm_metrics import LLMMetrics
from sona_observability.infrastructure.mcp_metrics import MCPMetrics
from sona_observability.infrastructure.memory_metrics import MemoryMetrics
from sona_observability.infrastructure.metrics_registry import MetricsRegistry
from sona_observability.infrastructure.middleware import ObservabilityMiddleware
from sona_observability.infrastructure.prometheus_exporter import PrometheusExporter
from sona_observability.infrastructure.rag_metrics import RAGMetrics
from sona_observability.infrastructure.request_metrics import RequestMetrics
from sona_observability.infrastructure.structured_logger import StructuredLogger
from sona_observability.infrastructure.tracer import Tracer


class ObservabilityRuntime:
    """Unified observability runtime combining metrics, tracing, and logging.

    Provides a single entry point for all observability operations and
    exposes specialized metric collectors for different subsystems.
    """

    def __init__(
        self,
        service_name: str = "sona-ai-os",
        sample_rate: float = 1.0,
    ) -> None:
        """Initialize the observability runtime.

        Args:
            service_name: Name of the service.
            sample_rate: Log sampling rate (0.0 to 1.0).
        """
        self._service_name = service_name

        # Core components
        self._metrics = MetricsRegistry()
        self._tracer = Tracer(service_name=service_name)
        self._logger = StructuredLogger(service_name=service_name, sample_rate=sample_rate)

        # Specialized collectors
        self._request_metrics = RequestMetrics(self._metrics)
        self._llm_metrics = LLMMetrics(self._metrics)
        self._memory_metrics = MemoryMetrics(self._metrics)
        self._rag_metrics = RAGMetrics(self._metrics)
        self._mcp_metrics = MCPMetrics(self._metrics)

        # Exporters and reporters
        self._prometheus = PrometheusExporter(self._metrics)
        self._health = HealthReporter()

        # Middleware
        self._middleware = ObservabilityMiddleware(
            tracer=self._tracer,
            registry=self._metrics,
            logger=self._logger,
        )

        # Correlation
        self._correlation = CorrelationManager()

    @property
    def service_name(self) -> str:
        """Return the service name."""
        return self._service_name

    @property
    def metrics(self) -> MetricsRegistry:
        """Access the metrics registry."""
        return self._metrics

    @property
    def tracer(self) -> Tracer:
        """Access the distributed tracer."""
        return self._tracer

    @property
    def logger(self) -> StructuredLogger:
        """Access the structured logger."""
        return self._logger

    @property
    def request_metrics(self) -> RequestMetrics:
        """Access the HTTP request metrics collector."""
        return self._request_metrics

    @property
    def llm_metrics(self) -> LLMMetrics:
        """Access the LLM metrics collector."""
        return self._llm_metrics

    @property
    def memory_metrics(self) -> MemoryMetrics:
        """Access the memory metrics collector."""
        return self._memory_metrics

    @property
    def rag_metrics(self) -> RAGMetrics:
        """Access the RAG metrics collector."""
        return self._rag_metrics

    @property
    def mcp_metrics(self) -> MCPMetrics:
        """Access the MCP metrics collector."""
        return self._mcp_metrics

    @property
    def prometheus(self) -> PrometheusExporter:
        """Access the Prometheus exporter."""
        return self._prometheus

    @property
    def health(self) -> HealthReporter:
        """Access the health reporter."""
        return self._health

    @property
    def middleware(self) -> ObservabilityMiddleware:
        """Access the observability middleware."""
        return self._middleware

    @property
    def correlation(self) -> type[CorrelationManager]:
        """Access the correlation manager class."""
        return CorrelationManager

    # --- Convenience methods ---

    def increment(self, name: str, value: float = 1.0, tags: dict[str, Any] | None = None) -> None:
        """Increment a counter metric."""
        self._metrics.increment(name, value, tags)

    def gauge_set(self, name: str, value: float, tags: dict[str, Any] | None = None) -> None:
        """Set a gauge metric."""
        self._metrics.gauge(name, value, tags)

    def record_histogram(self, name: str, value: float, tags: dict[str, Any] | None = None) -> None:
        """Record a histogram observation."""
        self._metrics.histogram(name, value, tags)

    def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
        """Start a tracing span."""
        return self._tracer.start_span(operation, parent)

    def end_span(self, span: SpanContext, status: str = "ok") -> None:
        """End a tracing span."""
        self._tracer.end_span(span, status)

    def log(self, level: LogLevel, message: str, context: dict[str, Any] | None = None) -> None:
        """Emit a structured log entry."""
        self._logger.log(level, message, context)

    def export_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        return self._prometheus.export()

    def health_report(self) -> dict[str, Any]:
        """Generate a health report."""
        return self._health.detailed_report()
