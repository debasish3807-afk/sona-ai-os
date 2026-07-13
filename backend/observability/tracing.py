"""Distributed tracing with OpenTelemetry-compatible export."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Span:
    """A single trace span."""

    span_id: str
    trace_id: str
    parent_id: str | None
    operation: str
    service: str
    start_time: float
    end_time: float | None = None
    status: str = "in_progress"
    attributes: dict[str, Any] = field(default_factory=dict)


class TracingManager:
    """Manages distributed traces and spans."""

    def __init__(self) -> None:
        self._spans: dict[str, Span] = {}
        self._traces: dict[str, list[str]] = {}

    def start_span(
        self,
        operation: str,
        service: str,
        parent_id: str | None = None,
    ) -> Span:
        """Start a new span.

        Args:
            operation: Name of the operation being traced.
            service: Service name.
            parent_id: Optional parent span ID for nesting.

        Returns:
            The created Span.
        """
        span_id = str(uuid.uuid4())

        if parent_id and parent_id in self._spans:
            trace_id = self._spans[parent_id].trace_id
        else:
            trace_id = str(uuid.uuid4())

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            operation=operation,
            service=service,
            start_time=time.time(),
        )

        self._spans[span_id] = span
        if trace_id not in self._traces:
            self._traces[trace_id] = []
        self._traces[trace_id].append(span_id)

        logger.debug("span_started", span_id=span_id, operation=operation)
        return span

    def end_span(self, span_id: str, status: str = "ok") -> None:
        """End a span.

        Args:
            span_id: The span to end.
            status: Final status (ok, error).
        """
        span = self._spans.get(span_id)
        if span:
            span.end_time = time.time()
            span.status = status
            logger.debug("span_ended", span_id=span_id, status=status)

    def get_trace(self, trace_id: str) -> list[Span]:
        """Get all spans for a trace.

        Args:
            trace_id: The trace identifier.

        Returns:
            List of spans in the trace.
        """
        span_ids = self._traces.get(trace_id, [])
        return [self._spans[sid] for sid in span_ids if sid in self._spans]

    def export_otlp(self) -> list[dict[str, Any]]:
        """Export spans in OpenTelemetry-compatible format.

        Returns:
            List of span dictionaries.
        """
        exported: list[dict[str, Any]] = []
        for span in self._spans.values():
            exported.append(
                {
                    "traceId": span.trace_id,
                    "spanId": span.span_id,
                    "parentSpanId": span.parent_id or "",
                    "operationName": span.operation,
                    "serviceName": span.service,
                    "startTime": span.start_time,
                    "endTime": span.end_time,
                    "status": span.status,
                    "attributes": span.attributes,
                }
            )
        return exported
