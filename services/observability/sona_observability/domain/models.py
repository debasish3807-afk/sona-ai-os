"""Domain models for the Observability service.

Defines the data structures used for metrics collection, distributed tracing,
and structured logging across all Sona AI OS services.
"""

from dataclasses import dataclass
from enum import StrEnum


class MetricType(StrEnum):
    """Types of metrics that can be collected.

    Determines how the metric value is aggregated and displayed
    in monitoring dashboards.
    """

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(StrEnum):
    """Severity levels for structured log entries.

    Used to classify log messages by importance and to control
    which messages are emitted based on configuration.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class SpanContext:
    """Context for a distributed tracing span.

    Carries trace correlation identifiers that propagate across service
    boundaries, enabling end-to-end request tracing.

    Attributes:
        trace_id: Unique identifier for the overall trace (request lifecycle).
        span_id: Unique identifier for this specific span within the trace.
        parent_span_id: Identifier of the parent span, or None for root spans.
        service_name: Name of the service that created this span.
        operation: Name of the operation being traced (e.g., "process_request").
    """

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    service_name: str = ""
    operation: str = ""
