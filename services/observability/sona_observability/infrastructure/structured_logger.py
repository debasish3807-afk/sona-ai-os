"""Structured logger implementing LoggingPort.

Provides JSON-formatted log entries with automatic fields (timestamp, level,
service, trace_id, span_id), context binding, log sampling, and enrichment.
"""

from __future__ import annotations

import json
import random
import time
from typing import Any

from sona_observability.application.ports import LoggingPort
from sona_observability.domain.models import LogLevel


class StructuredLogger(LoggingPort):
    """JSON-structured logger with context binding and sampling.

    Produces log entries as JSON objects with automatic fields and
    supports context binding for request-scoped logging.
    """

    def __init__(
        self,
        service_name: str = "sona-ai-os",
        bound_context: dict[str, Any] | None = None,
        sample_rate: float = 1.0,
        sink: Any | None = None,
    ) -> None:
        """Initialize the structured logger.

        Args:
            service_name: The name of the service emitting logs.
            bound_context: Pre-bound context fields.
            sample_rate: Sampling rate between 0.0 and 1.0.
            sink: Optional output sink (callable accepting str).
        """
        self._service_name = service_name
        self._bound_context: dict[str, Any] = bound_context or {}
        self._sample_rate = max(0.0, min(1.0, sample_rate))
        self._sink = sink
        self._entries: list[dict[str, Any]] = []

    @property
    def entries(self) -> list[dict[str, Any]]:
        """Return captured log entries (useful for testing)."""
        return list(self._entries)

    @property
    def sample_rate(self) -> float:
        """Return the configured sample rate."""
        return self._sample_rate

    def log(self, level: LogLevel, message: str, context: dict[str, Any] | None = None) -> None:
        """Emit a structured log entry.

        Applies sampling, merges bound context, and produces a JSON entry.

        Args:
            level: The severity level of the log entry.
            message: The log message.
            context: Optional structured context data to include.
        """
        # Apply sampling
        if self._sample_rate < 1.0 and random.random() > self._sample_rate:
            return

        entry: dict[str, Any] = {
            "timestamp": time.time(),
            "level": str(level),
            "service": self._service_name,
            "message": message,
        }

        # Merge bound context
        if self._bound_context:
            entry.update(self._bound_context)

        # Merge call-site context
        if context:
            entry.update(context)

        self._entries.append(entry)

        if self._sink is not None:
            self._sink(json.dumps(entry))

    def with_context(self, **kwargs: Any) -> StructuredLogger:
        """Create a new logger instance with additional bound context.

        Args:
            **kwargs: Key-value pairs to bind to all subsequent log entries.

        Returns:
            A new StructuredLogger instance with the additional context bound.
        """
        new_context = {**self._bound_context, **kwargs}
        logger = StructuredLogger(
            service_name=self._service_name,
            bound_context=new_context,
            sample_rate=self._sample_rate,
            sink=self._sink,
        )
        # Share entries list for testing purposes
        logger._entries = self._entries
        return logger

    def with_request_id(self, request_id: str) -> StructuredLogger:
        """Create a new logger enriched with a request ID.

        Args:
            request_id: The request identifier to bind.

        Returns:
            A new StructuredLogger with request_id in context.
        """
        return self.with_context(request_id=request_id)

    def with_user_id(self, user_id: str) -> StructuredLogger:
        """Create a new logger enriched with a user ID.

        Args:
            user_id: The user identifier to bind.

        Returns:
            A new StructuredLogger with user_id in context.
        """
        return self.with_context(user_id=user_id)

    def with_trace(self, trace_id: str, span_id: str) -> StructuredLogger:
        """Create a new logger enriched with trace context.

        Args:
            trace_id: The trace identifier.
            span_id: The span identifier.

        Returns:
            A new StructuredLogger with trace context bound.
        """
        return self.with_context(trace_id=trace_id, span_id=span_id)
