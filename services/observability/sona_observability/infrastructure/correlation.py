"""Correlation ID manager for request tracing across services.

Generates and propagates correlation IDs (request_id, trace_id)
through async context using contextvars, and supports header
injection/extraction for cross-service propagation.
"""

from __future__ import annotations

import contextvars
import uuid

# Context variables for correlation IDs
_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")
_span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("span_id", default="")

# Header names for propagation
HEADER_REQUEST_ID = "x-request-id"
HEADER_TRACE_ID = "x-trace-id"
HEADER_SPAN_ID = "x-span-id"


class CorrelationManager:
    """Manages correlation IDs for distributed request tracing.

    Provides generation, propagation through async context (contextvars),
    extraction from incoming headers, and injection into outgoing headers.
    """

    @staticmethod
    def generate_request_id() -> str:
        """Generate a new unique request ID."""
        return uuid.uuid4().hex

    @staticmethod
    def generate_trace_id() -> str:
        """Generate a new unique trace ID."""
        return uuid.uuid4().hex

    @staticmethod
    def generate_span_id() -> str:
        """Generate a new unique span ID."""
        return uuid.uuid4().hex[:16]

    @staticmethod
    def set_request_id(request_id: str) -> None:
        """Set the current request ID in context."""
        _request_id_var.set(request_id)

    @staticmethod
    def get_request_id() -> str:
        """Get the current request ID from context."""
        return _request_id_var.get()

    @staticmethod
    def set_trace_id(trace_id: str) -> None:
        """Set the current trace ID in context."""
        _trace_id_var.set(trace_id)

    @staticmethod
    def get_trace_id() -> str:
        """Get the current trace ID from context."""
        return _trace_id_var.get()

    @staticmethod
    def set_span_id(span_id: str) -> None:
        """Set the current span ID in context."""
        _span_id_var.set(span_id)

    @staticmethod
    def get_span_id() -> str:
        """Get the current span ID from context."""
        return _span_id_var.get()

    @staticmethod
    def extract_from_headers(headers: dict[str, str]) -> dict[str, str]:
        """Extract correlation IDs from incoming request headers.

        Args:
            headers: Incoming HTTP headers (case-insensitive lookup).

        Returns:
            Dictionary of extracted correlation IDs.
        """
        # Normalize headers to lowercase keys
        normalized = {k.lower(): v for k, v in headers.items()}
        result: dict[str, str] = {}

        if HEADER_REQUEST_ID in normalized:
            result["request_id"] = normalized[HEADER_REQUEST_ID]
        if HEADER_TRACE_ID in normalized:
            result["trace_id"] = normalized[HEADER_TRACE_ID]
        if HEADER_SPAN_ID in normalized:
            result["span_id"] = normalized[HEADER_SPAN_ID]

        return result

    @staticmethod
    def inject_into_headers(headers: dict[str, str] | None = None) -> dict[str, str]:
        """Inject current correlation IDs into outgoing headers.

        Args:
            headers: Optional existing headers to augment.

        Returns:
            Headers dictionary with correlation IDs injected.
        """
        result = dict(headers) if headers else {}

        request_id = _request_id_var.get()
        trace_id = _trace_id_var.get()
        span_id = _span_id_var.get()

        if request_id:
            result[HEADER_REQUEST_ID] = request_id
        if trace_id:
            result[HEADER_TRACE_ID] = trace_id
        if span_id:
            result[HEADER_SPAN_ID] = span_id

        return result

    @staticmethod
    def initialize(
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, str]:
        """Initialize correlation context, generating IDs if not provided.

        Args:
            request_id: Optional pre-existing request ID.
            trace_id: Optional pre-existing trace ID.

        Returns:
            Dictionary of the initialized correlation IDs.
        """
        req_id = request_id or CorrelationManager.generate_request_id()
        tr_id = trace_id or CorrelationManager.generate_trace_id()

        _request_id_var.set(req_id)
        _trace_id_var.set(tr_id)

        return {"request_id": req_id, "trace_id": tr_id}

    @staticmethod
    def clear() -> None:
        """Clear all correlation IDs from context."""
        _request_id_var.set("")
        _trace_id_var.set("")
        _span_id_var.set("")
