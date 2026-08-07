"""Observability middleware for automatic request instrumentation.

Provides a middleware class that automatically starts spans, records
request metrics, propagates correlation IDs, enriches logs with
request context, and measures response time.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from sona_observability.infrastructure.correlation import CorrelationManager
from sona_observability.infrastructure.metrics_registry import MetricsRegistry
from sona_observability.infrastructure.request_metrics import RequestMetrics
from sona_observability.infrastructure.structured_logger import StructuredLogger
from sona_observability.infrastructure.tracer import Tracer


@dataclass
class RequestContext:
    """Context created by middleware for each request."""

    method: str
    path: str
    request_id: str
    trace_id: str
    span_id: str
    start_time: float


class ObservabilityMiddleware:
    """Middleware that instruments incoming HTTP requests.

    Automatically:
    - Starts a span for each request
    - Records request metrics (count, duration, status)
    - Propagates correlation IDs
    - Enriches logs with request context
    - Measures response time
    """

    def __init__(
        self,
        tracer: Tracer,
        registry: MetricsRegistry,
        logger: StructuredLogger,
    ) -> None:
        self._tracer = tracer
        self._request_metrics = RequestMetrics(registry)
        self._logger = logger

    def before_request(
        self, method: str, path: str, headers: dict[str, str] | None = None
    ) -> RequestContext:
        """Process an incoming request before handling.

        Creates a span, sets up correlation IDs, and logs the request.

        Args:
            method: HTTP method.
            path: Request path.
            headers: Incoming request headers.

        Returns:
            RequestContext to be passed to after_request.
        """
        # Extract or generate correlation IDs
        extracted: dict[str, str] = {}
        if headers:
            extracted = CorrelationManager.extract_from_headers(headers)

        ids = CorrelationManager.initialize(
            request_id=extracted.get("request_id"),
            trace_id=extracted.get("trace_id"),
        )

        # Start a span for this request
        parent_context = None
        if headers:
            parent_context = self._tracer.extract_context(headers)

        span = self._tracer.start_span(f"{method} {path}", parent=parent_context)
        CorrelationManager.set_span_id(span.span_id)

        # Increment active requests
        self._request_metrics.increment_active()

        # Log the incoming request
        self._logger.log(
            level=__import__(
                "sona_observability.domain.models", fromlist=["LogLevel"]
            ).LogLevel.INFO,
            message=f"Request started: {method} {path}",
            context={
                "request_id": ids["request_id"],
                "trace_id": ids["trace_id"],
                "span_id": span.span_id,
                "method": method,
                "path": path,
            },
        )

        return RequestContext(
            method=method,
            path=path,
            request_id=ids["request_id"],
            trace_id=ids["trace_id"],
            span_id=span.span_id,
            start_time=time.monotonic(),
        )

    def after_request(
        self, ctx: RequestContext, status_code: int, error: str | None = None
    ) -> dict[str, Any]:
        """Process a request after handling.

        Records metrics, ends the span, and logs the response.

        Args:
            ctx: The RequestContext from before_request.
            status_code: HTTP response status code.
            error: Optional error message.

        Returns:
            Dictionary with response headers for correlation propagation.
        """
        duration_ms = (time.monotonic() - ctx.start_time) * 1000.0
        status = "error" if error or status_code >= 500 else "ok"

        # End span
        from sona_observability.domain.models import LogLevel, SpanContext

        span = SpanContext(
            trace_id=ctx.trace_id,
            span_id=ctx.span_id,
            service_name=self._tracer.service_name,
            operation=f"{ctx.method} {ctx.path}",
        )
        self._tracer.end_span(span, status=status)

        # Record metrics
        self._request_metrics.record_request(ctx.method, ctx.path, status_code, duration_ms)
        self._request_metrics.decrement_active()

        # Log the response
        log_level = LogLevel.ERROR if status_code >= 500 else LogLevel.INFO
        self._logger.log(
            level=log_level,
            message=f"Request completed: {ctx.method} {ctx.path} -> {status_code}",
            context={
                "request_id": ctx.request_id,
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id,
                "method": ctx.method,
                "path": ctx.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        # Return correlation headers for response
        return CorrelationManager.inject_into_headers()
