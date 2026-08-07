"""Abstract port interfaces for the Observability service.

Defines the contracts that infrastructure adapters must implement
to provide metrics collection, distributed tracing, and structured logging.
"""

from abc import ABC, abstractmethod
from typing import Any

from sona_observability.domain.models import LogLevel, SpanContext


class MetricsPort(ABC):
    """Port for metrics collection and reporting.

    Infrastructure adapters implement this port to send metrics
    to backends such as Prometheus, Datadog, or CloudWatch.
    """

    @abstractmethod
    def increment(self, name: str, value: float = 1.0, tags: dict[str, Any] | None = None) -> None:
        """Increment a counter metric.

        Args:
            name: The metric name (e.g., "requests_total").
            value: The value to increment by (default 1.0).
            tags: Optional key-value tags for metric dimensions.
        """
        ...

    @abstractmethod
    def gauge(self, name: str, value: float, tags: dict[str, Any] | None = None) -> None:
        """Set a gauge metric to a specific value.

        Args:
            name: The metric name (e.g., "active_connections").
            value: The current value to set.
            tags: Optional key-value tags for metric dimensions.
        """
        ...

    @abstractmethod
    def histogram(self, name: str, value: float, tags: dict[str, Any] | None = None) -> None:
        """Record a value in a histogram metric.

        Args:
            name: The metric name (e.g., "request_duration_ms").
            value: The observed value to record.
            tags: Optional key-value tags for metric dimensions.
        """
        ...


class TracingPort(ABC):
    """Port for distributed tracing operations.

    Infrastructure adapters implement this port to integrate with
    tracing backends such as OpenTelemetry, Jaeger, or Zipkin.
    """

    @abstractmethod
    def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
        """Start a new tracing span.

        Args:
            operation: Name of the operation being traced.
            parent: Optional parent span context for nested spans.

        Returns:
            A SpanContext representing the newly created span.
        """
        ...

    @abstractmethod
    def end_span(self, span: SpanContext, status: str = "ok") -> None:
        """End an active tracing span.

        Args:
            span: The span context to end.
            status: The completion status (e.g., "ok", "error").
        """
        ...

    @abstractmethod
    def inject_context(self, span: SpanContext) -> dict[str, str]:
        """Inject span context into a carrier for cross-service propagation.

        Args:
            span: The span context to propagate.

        Returns:
            A dictionary of headers/metadata for context propagation.
        """
        ...


class LoggingPort(ABC):
    """Port for structured logging operations.

    Infrastructure adapters implement this port to send structured
    log entries to backends such as ELK, CloudWatch Logs, or stdout.
    """

    @abstractmethod
    def log(self, level: LogLevel, message: str, context: dict[str, Any] | None = None) -> None:
        """Emit a structured log entry.

        Args:
            level: The severity level of the log entry.
            message: The log message.
            context: Optional structured context data to include.
        """
        ...

    @abstractmethod
    def with_context(self, **kwargs: Any) -> "LoggingPort":
        """Create a new logger instance with additional bound context.

        Args:
            **kwargs: Key-value pairs to bind to all subsequent log entries.

        Returns:
            A new LoggingPort instance with the additional context bound.
        """
        ...
