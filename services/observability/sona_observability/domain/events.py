"""Domain events for the Observability service.

These events are emitted when significant observability actions occur,
enabling other bounded contexts to react to telemetry changes.
"""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class MetricRecordedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a metric value is recorded."""

    name: str = ""
    metric_type: str = ""
    value: float = 0.0


@dataclass(frozen=True)
class SpanStartedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a new tracing span is started."""

    trace_id: str = ""
    span_id: str = ""
    operation: str = ""


@dataclass(frozen=True)
class SpanEndedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a tracing span is completed."""

    trace_id: str = ""
    span_id: str = ""
    duration_ms: float = 0.0
    status: str = "ok"


@dataclass(frozen=True)
class AlertTriggeredEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a metric crosses a configured alert threshold."""

    metric_name: str = ""
    threshold: float = 0.0
    current_value: float = 0.0
