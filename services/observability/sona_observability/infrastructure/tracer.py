"""Distributed tracer implementing TracingPort.

Provides span creation with parent-child relationships, UUID-based ID
generation, duration tracking, context propagation, and span attributes.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from sona_observability.application.ports import TracingPort
from sona_observability.domain.models import SpanContext


@dataclass
class SpanRecord:
    """Internal record for an active span with timing and attributes."""

    context: SpanContext
    start_time: float
    end_time: float | None = None
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        """Compute span duration in milliseconds."""
        if self.end_time is None:
            return (time.monotonic() - self.start_time) * 1000.0
        return (self.end_time - self.start_time) * 1000.0


class Tracer(TracingPort):
    """Distributed tracer with parent-child span relationships.

    Generates UUID-based trace and span IDs, tracks active spans,
    computes durations, and supports context propagation.
    """

    def __init__(self, service_name: str = "sona-ai-os") -> None:
        self._service_name = service_name
        self._active_spans: dict[str, SpanRecord] = {}
        self._completed_spans: list[SpanRecord] = []

    @property
    def service_name(self) -> str:
        """Return the service name for this tracer."""
        return self._service_name

    @property
    def active_spans(self) -> dict[str, SpanRecord]:
        """Return currently active spans."""
        return dict(self._active_spans)

    @property
    def completed_spans(self) -> list[SpanRecord]:
        """Return list of completed spans."""
        return list(self._completed_spans)

    def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
        """Start a new tracing span.

        Args:
            operation: Name of the operation being traced.
            parent: Optional parent span context for nested spans.

        Returns:
            A SpanContext representing the newly created span.
        """
        trace_id = parent.trace_id if parent else uuid.uuid4().hex
        span_id = uuid.uuid4().hex
        parent_span_id = parent.span_id if parent else None

        context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            service_name=self._service_name,
            operation=operation,
        )

        record = SpanRecord(context=context, start_time=time.monotonic())
        self._active_spans[span_id] = record
        return context

    def end_span(self, span: SpanContext, status: str = "ok") -> None:
        """End an active tracing span.

        Args:
            span: The span context to end.
            status: The completion status (e.g., "ok", "error").
        """
        record = self._active_spans.pop(span.span_id, None)
        if record is not None:
            record.end_time = time.monotonic()
            record.status = status
            self._completed_spans.append(record)

    def inject_context(self, span: SpanContext) -> dict[str, str]:
        """Inject span context into headers for cross-service propagation.

        Uses W3C Trace Context format for traceparent header.

        Args:
            span: The span context to propagate.

        Returns:
            A dictionary of headers for context propagation.
        """
        traceparent = f"00-{span.trace_id}-{span.span_id}-01"
        headers: dict[str, str] = {"traceparent": traceparent}
        if span.service_name:
            headers["tracestate"] = f"service={span.service_name}"
        return headers

    def extract_context(self, headers: dict[str, str]) -> SpanContext | None:
        """Extract span context from incoming headers.

        Parses W3C Trace Context traceparent header.

        Args:
            headers: Incoming request headers.

        Returns:
            A SpanContext if traceparent header is present, None otherwise.
        """
        traceparent = headers.get("traceparent")
        if not traceparent:
            return None

        parts = traceparent.split("-")
        if len(parts) < 4:
            return None

        trace_id = parts[1]
        span_id = parts[2]

        service_name = ""
        tracestate = headers.get("tracestate", "")
        if tracestate.startswith("service="):
            service_name = tracestate[len("service=") :]

        return SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            service_name=service_name,
        )

    def set_attribute(self, span: SpanContext, key: str, value: Any) -> None:
        """Set an attribute on an active span.

        Args:
            span: The span to add the attribute to.
            key: Attribute key.
            value: Attribute value.
        """
        record = self._active_spans.get(span.span_id)
        if record is not None:
            record.attributes[key] = value

    def get_span_duration(self, span: SpanContext) -> float | None:
        """Get the duration of a completed span in milliseconds.

        Args:
            span: The span context to look up.

        Returns:
            Duration in milliseconds, or None if span not found in completed spans.
        """
        for record in self._completed_spans:
            if record.context.span_id == span.span_id:
                return record.duration_ms
        return None
