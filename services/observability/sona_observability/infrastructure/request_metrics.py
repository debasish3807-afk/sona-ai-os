"""Pre-defined metrics collector for HTTP requests.

Provides standardized metrics for monitoring HTTP request traffic
including total count, duration, and active request gauges.
"""

from __future__ import annotations

from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class RequestMetrics:
    """Collects standard HTTP request metrics.

    Metrics:
        - http_requests_total: Counter with labels method, path, status
        - http_request_duration_ms: Histogram with labels method, path
        - http_requests_active: Gauge for currently active requests
    """

    REQUESTS_TOTAL = "http_requests_total"
    REQUEST_DURATION_MS = "http_request_duration_ms"
    REQUESTS_ACTIVE = "http_requests_active"

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry

    def record_request(self, method: str, path: str, status: int, duration_ms: float) -> None:
        """Record a completed HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path.
            status: HTTP status code.
            duration_ms: Request duration in milliseconds.
        """
        tags = {"method": method, "path": path, "status": str(status)}
        self._registry.increment(self.REQUESTS_TOTAL, tags=tags)
        self._registry.histogram(
            self.REQUEST_DURATION_MS,
            duration_ms,
            tags={"method": method, "path": path},
        )

    def increment_active(self) -> None:
        """Increment the active requests gauge."""
        current = self._registry.get_gauge(self.REQUESTS_ACTIVE)
        self._registry.gauge(self.REQUESTS_ACTIVE, current + 1)

    def decrement_active(self) -> None:
        """Decrement the active requests gauge."""
        current = self._registry.get_gauge(self.REQUESTS_ACTIVE)
        self._registry.gauge(self.REQUESTS_ACTIVE, max(0, current - 1))
