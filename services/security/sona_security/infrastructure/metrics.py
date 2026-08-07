"""Security metrics collection.

Tracks authentication, authorization, safety, and rate limit metrics
for monitoring and alerting.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class MetricCounter:
    """A simple counter metric."""

    name: str
    value: int = 0
    labels: dict[str, str] = field(default_factory=dict)

    def increment(self, amount: int = 1) -> None:
        """Increment the counter."""
        self.value += amount

    def reset(self) -> None:
        """Reset the counter to zero."""
        self.value = 0


class SecurityMetrics:
    """Security metrics collector."""

    def __init__(self) -> None:
        self._counters: dict[str, MetricCounter] = {}
        self._init_default_counters()

    def _init_default_counters(self) -> None:
        """Initialize default security metric counters."""
        default_metrics = [
            "auth_success_total",
            "auth_failure_total",
            "token_validation_total",
            "token_validation_failure_total",
            "permission_granted_total",
            "permission_denied_total",
            "safety_check_total",
            "safety_check_blocked_total",
            "rate_limit_hit_total",
            "api_key_created_total",
            "api_key_revoked_total",
            "tool_access_allowed_total",
            "tool_access_denied_total",
        ]
        for name in default_metrics:
            self._counters[name] = MetricCounter(name=name)

    def increment(self, metric_name: str, amount: int = 1) -> None:
        """Increment a metric counter."""
        if metric_name not in self._counters:
            self._counters[metric_name] = MetricCounter(name=metric_name)
        self._counters[metric_name].increment(amount)

    def get(self, metric_name: str) -> int:
        """Get the current value of a metric."""
        counter = self._counters.get(metric_name)
        return counter.value if counter else 0

    def get_all(self) -> dict[str, int]:
        """Get all metric values."""
        return {name: counter.value for name, counter in self._counters.items()}

    def reset(self, metric_name: str) -> None:
        """Reset a specific metric to zero."""
        if metric_name in self._counters:
            self._counters[metric_name].reset()

    def reset_all(self) -> None:
        """Reset all metrics to zero."""
        for counter in self._counters.values():
            counter.reset()

    def snapshot(self) -> dict[str, Any]:
        """Get a snapshot of all metrics for export."""
        return {
            "metrics": self.get_all(),
            "counter_count": len(self._counters),
        }

    def record_auth_success(self) -> None:
        """Record a successful authentication."""
        self.increment("auth_success_total")

    def record_auth_failure(self) -> None:
        """Record a failed authentication."""
        self.increment("auth_failure_total")

    def record_token_validation(self, success: bool = True) -> None:
        """Record a token validation attempt."""
        self.increment("token_validation_total")
        if not success:
            self.increment("token_validation_failure_total")

    def record_permission_check(self, granted: bool = True) -> None:
        """Record a permission check."""
        if granted:
            self.increment("permission_granted_total")
        else:
            self.increment("permission_denied_total")

    def record_safety_check(self, blocked: bool = False) -> None:
        """Record a safety check."""
        self.increment("safety_check_total")
        if blocked:
            self.increment("safety_check_blocked_total")

    def record_rate_limit_hit(self) -> None:
        """Record a rate limit hit."""
        self.increment("rate_limit_hit_total")
