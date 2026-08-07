"""Integration tests for the ObservabilityRuntime and DI factory.

Tests verify the full runtime orchestrator works correctly with all
components wired together, and that the factory creates valid instances.
"""

from sona_observability.domain.models import LogLevel, SpanContext
from sona_observability.infrastructure.di import create_observability_runtime
from sona_observability.infrastructure.health_reporter import HealthReporter, HealthStatus
from sona_observability.infrastructure.llm_metrics import LLMMetrics
from sona_observability.infrastructure.mcp_metrics import MCPMetrics
from sona_observability.infrastructure.memory_metrics import MemoryMetrics
from sona_observability.infrastructure.metrics_registry import MetricsRegistry
from sona_observability.infrastructure.middleware import ObservabilityMiddleware
from sona_observability.infrastructure.observability_runtime import ObservabilityRuntime
from sona_observability.infrastructure.prometheus_exporter import PrometheusExporter
from sona_observability.infrastructure.rag_metrics import RAGMetrics
from sona_observability.infrastructure.request_metrics import RequestMetrics
from sona_observability.infrastructure.structured_logger import StructuredLogger
from sona_observability.infrastructure.tracer import Tracer


class TestRuntimeCreation:
    """Tests for runtime creation and configuration."""

    def test_create_with_defaults(self) -> None:
        """Runtime can be created with default settings."""
        runtime = ObservabilityRuntime()
        assert runtime.service_name == "sona-ai-os"

    def test_create_with_custom_service_name(self) -> None:
        """Runtime can be created with custom service name."""
        runtime = ObservabilityRuntime(service_name="ai-kernel")
        assert runtime.service_name == "ai-kernel"

    def test_create_with_sample_rate(self) -> None:
        """Runtime can be created with log sample rate."""
        runtime = ObservabilityRuntime(sample_rate=0.5)
        assert runtime.logger.sample_rate == 0.5


class TestRuntimeComponents:
    """Tests for accessing runtime components."""

    def test_metrics_property(self) -> None:
        """Runtime exposes MetricsRegistry."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.metrics, MetricsRegistry)

    def test_tracer_property(self) -> None:
        """Runtime exposes Tracer."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.tracer, Tracer)

    def test_logger_property(self) -> None:
        """Runtime exposes StructuredLogger."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.logger, StructuredLogger)

    def test_request_metrics_property(self) -> None:
        """Runtime exposes RequestMetrics."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.request_metrics, RequestMetrics)

    def test_llm_metrics_property(self) -> None:
        """Runtime exposes LLMMetrics."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.llm_metrics, LLMMetrics)

    def test_memory_metrics_property(self) -> None:
        """Runtime exposes MemoryMetrics."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.memory_metrics, MemoryMetrics)

    def test_rag_metrics_property(self) -> None:
        """Runtime exposes RAGMetrics."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.rag_metrics, RAGMetrics)

    def test_mcp_metrics_property(self) -> None:
        """Runtime exposes MCPMetrics."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.mcp_metrics, MCPMetrics)

    def test_prometheus_property(self) -> None:
        """Runtime exposes PrometheusExporter."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.prometheus, PrometheusExporter)

    def test_health_property(self) -> None:
        """Runtime exposes HealthReporter."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.health, HealthReporter)

    def test_middleware_property(self) -> None:
        """Runtime exposes ObservabilityMiddleware."""
        runtime = ObservabilityRuntime()
        assert isinstance(runtime.middleware, ObservabilityMiddleware)


class TestRuntimeConvenienceMethods:
    """Tests for runtime convenience methods."""

    def test_increment(self) -> None:
        """Convenience increment delegates to metrics registry."""
        runtime = ObservabilityRuntime()
        runtime.increment("test_counter")
        assert runtime.metrics.get_counter("test_counter") == 1.0

    def test_increment_with_tags(self) -> None:
        """Convenience increment supports tags."""
        runtime = ObservabilityRuntime()
        runtime.increment("test", tags={"env": "prod"})
        assert runtime.metrics.get_counter("test", tags={"env": "prod"}) == 1.0

    def test_gauge_set(self) -> None:
        """Convenience gauge_set delegates to metrics registry."""
        runtime = ObservabilityRuntime()
        runtime.gauge_set("temperature", 42.0)
        assert runtime.metrics.get_gauge("temperature") == 42.0

    def test_record_histogram(self) -> None:
        """Convenience record_histogram delegates to metrics registry."""
        runtime = ObservabilityRuntime()
        runtime.record_histogram("duration_ms", 150.0)
        assert runtime.metrics.get_histogram_values("duration_ms") == [150.0]

    def test_start_and_end_span(self) -> None:
        """Convenience span methods delegate to tracer."""
        runtime = ObservabilityRuntime()
        span = runtime.start_span("test_op")
        assert isinstance(span, SpanContext)
        runtime.end_span(span)
        assert len(runtime.tracer.completed_spans) == 1

    def test_log(self) -> None:
        """Convenience log method delegates to logger."""
        runtime = ObservabilityRuntime()
        runtime.log(LogLevel.INFO, "Test message")
        assert len(runtime.logger.entries) == 1
        assert runtime.logger.entries[0]["message"] == "Test message"

    def test_export_metrics(self) -> None:
        """export_metrics returns Prometheus format."""
        runtime = ObservabilityRuntime()
        runtime.increment("test")
        output = runtime.export_metrics()
        assert "test" in output

    def test_health_report(self) -> None:
        """health_report returns detailed report."""
        runtime = ObservabilityRuntime()
        runtime.health.register_component("db")
        report = runtime.health_report()
        assert "status" in report
        assert "components" in report


class TestRuntimeIntegration:
    """Integration tests for full request lifecycle."""

    def test_full_request_lifecycle(self) -> None:
        """Full request lifecycle through middleware."""
        runtime = ObservabilityRuntime(service_name="test-svc")
        mw = runtime.middleware

        ctx = mw.before_request("POST", "/v1/chat")
        mw.after_request(ctx, 200)

        # Verify metrics recorded
        assert (
            runtime.metrics.get_counter(
                "http_requests_total",
                tags={"method": "POST", "path": "/v1/chat", "status": "200"},
            )
            == 1.0
        )
        # Verify span completed
        assert len(runtime.tracer.completed_spans) == 1
        # Verify log entries
        assert len(runtime.logger.entries) >= 2

    def test_llm_and_request_metrics_together(self) -> None:
        """LLM metrics and request metrics share the same registry."""
        runtime = ObservabilityRuntime()
        runtime.llm_metrics.record_request("openai", "gpt-4", 500.0, 100, 50)
        runtime.request_metrics.record_request("POST", "/v1/chat", 200, 600.0)

        # Both should appear in export
        output = runtime.export_metrics()
        assert "llm_requests_total" in output
        assert "http_requests_total" in output

    def test_health_with_degraded_component(self) -> None:
        """Health report reflects degraded component."""
        runtime = ObservabilityRuntime()
        runtime.health.register_component("database")
        runtime.health.update_status("database", HealthStatus.DEGRADED, "High latency")
        report = runtime.health_report()
        assert report["status"] == "degraded"

    def test_span_with_child(self) -> None:
        """Parent-child span relationship through runtime."""
        runtime = ObservabilityRuntime()
        parent = runtime.start_span("parent_op")
        child = runtime.tracer.start_span("child_op", parent=parent)
        runtime.end_span(child)
        runtime.end_span(parent)
        assert len(runtime.tracer.completed_spans) == 2

    def test_log_with_trace_context(self) -> None:
        """Logging with trace context through runtime."""
        runtime = ObservabilityRuntime()
        span = runtime.start_span("op")
        scoped_logger = runtime.logger.with_trace(span.trace_id, span.span_id)
        scoped_logger.log(LogLevel.INFO, "Processing")
        entry = runtime.logger.entries[0]
        assert entry["trace_id"] == span.trace_id
        assert entry["span_id"] == span.span_id


class TestDIFactory:
    """Tests for the dependency injection factory."""

    def test_factory_creates_runtime(self) -> None:
        """Factory creates an ObservabilityRuntime."""
        runtime = create_observability_runtime()
        assert isinstance(runtime, ObservabilityRuntime)

    def test_factory_default_service_name(self) -> None:
        """Factory uses default service name."""
        runtime = create_observability_runtime()
        assert runtime.service_name == "sona-ai-os"

    def test_factory_custom_service_name(self) -> None:
        """Factory accepts custom service name."""
        runtime = create_observability_runtime(service_name="gateway")
        assert runtime.service_name == "gateway"

    def test_factory_custom_sample_rate(self) -> None:
        """Factory accepts custom sample rate."""
        runtime = create_observability_runtime(sample_rate=0.1)
        assert runtime.logger.sample_rate == 0.1

    def test_factory_components_wired(self) -> None:
        """Factory creates runtime with all components properly wired."""
        runtime = create_observability_runtime(service_name="ai-kernel")
        # Verify tracer uses same service name
        assert runtime.tracer.service_name == "ai-kernel"
        # Verify all components are present
        assert runtime.metrics is not None
        assert runtime.tracer is not None
        assert runtime.logger is not None
        assert runtime.prometheus is not None
        assert runtime.health is not None
        assert runtime.middleware is not None

    def test_factory_shared_registry(self) -> None:
        """Factory wires shared metrics registry across components."""
        runtime = create_observability_runtime()
        runtime.llm_metrics.record_request("openai", "gpt-4", 100.0, 50, 25)
        # Should be accessible from the main registry
        assert (
            runtime.metrics.get_counter(
                "llm_requests_total",
                tags={"provider": "openai", "model": "gpt-4"},
            )
            == 1.0
        )
