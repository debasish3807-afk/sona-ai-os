"""Security metrics — tracks request counts, errors, and latency.

Provides real-time counters for monitoring and alerting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SecurityMetrics:
    """Tracks security-relevant metrics."""

    total_requests: int = 0
    total_errors: int = 0
    rate_limited_count: int = 0
    auth_failures: int = 0
    permission_denials: int = 0
    _latencies: list[float] = field(default_factory=list)

    def record_request(self) -> None:
        """Record a request."""
        self.total_requests += 1

    def record_error(self) -> None:
        """Record an error response."""
        self.total_errors += 1

    def record_rate_limit(self) -> None:
        """Record a rate-limited request."""
        self.rate_limited_count += 1

    def record_auth_failure(self) -> None:
        """Record an authentication failure."""
        self.auth_failures += 1

    def record_permission_denial(self) -> None:
        """Record a permission denial."""
        self.permission_denials += 1

    def record_latency(self, ms: float) -> None:
        """Record request latency in ms."""
        self._latencies.append(ms)
        # Keep last 1000 entries
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-1000:]

    @property
    def average_latency_ms(self) -> float:
        if not self._latencies:
            return 0.0
        return sum(self._latencies) / len(self._latencies)

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "rate_limited_count": self.rate_limited_count,
            "auth_failures": self.auth_failures,
            "permission_denials": self.permission_denials,
            "average_latency_ms": round(self.average_latency_ms, 2),
            "error_rate": round(self.error_rate, 4),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.total_requests = 0
        self.total_errors = 0
        self.rate_limited_count = 0
        self.auth_failures = 0
        self.permission_denials = 0
        self._latencies.clear()
