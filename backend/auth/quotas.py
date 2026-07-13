"""API quota management for rate limiting and usage tracking."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class APIQuota:
    """API quota configuration for a user."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000


@dataclass
class _UsageWindow:
    """Tracks request timestamps within a window."""

    timestamps: list[float] = field(default_factory=list)

    def count_in_window(self, window_seconds: float) -> int:
        """Count requests within the time window."""
        cutoff = time.time() - window_seconds
        self.timestamps = [t for t in self.timestamps if t > cutoff]
        return len(self.timestamps)

    def record(self) -> None:
        """Record a new request timestamp."""
        self.timestamps.append(time.time())


class QuotaManager:
    """Manages API quotas and usage tracking per user."""

    def __init__(self) -> None:
        self._quotas: dict[str, APIQuota] = {}
        self._usage: dict[str, _UsageWindow] = {}
        self._lock = threading.Lock()

    def set_quota(self, user_id: str, quota: APIQuota) -> None:
        """Set the quota for a user."""
        with self._lock:
            self._quotas[user_id] = quota
            logger.info("quota_set", user_id=user_id)

    def check_quota(self, user_id: str) -> tuple[bool, dict]:
        """Check if user is within quota limits.

        Returns (allowed, details) where details has remaining counts.
        """
        with self._lock:
            quota = self._quotas.get(user_id, APIQuota())
            usage = self._usage.get(user_id, _UsageWindow())

            minute_count = usage.count_in_window(60)
            hour_count = usage.count_in_window(3600)
            day_count = usage.count_in_window(86400)

            details = {
                "minute_remaining": max(0, quota.requests_per_minute - minute_count),
                "hour_remaining": max(0, quota.requests_per_hour - hour_count),
                "day_remaining": max(0, quota.requests_per_day - day_count),
            }

            allowed = (
                minute_count < quota.requests_per_minute
                and hour_count < quota.requests_per_hour
                and day_count < quota.requests_per_day
            )
            return allowed, details

    def record_request(self, user_id: str) -> None:
        """Record a request for quota tracking."""
        with self._lock:
            if user_id not in self._usage:
                self._usage[user_id] = _UsageWindow()
            self._usage[user_id].record()

    def get_usage(self, user_id: str) -> dict:
        """Get current usage stats for a user."""
        with self._lock:
            usage = self._usage.get(user_id, _UsageWindow())
            return {
                "minute": usage.count_in_window(60),
                "hour": usage.count_in_window(3600),
                "day": usage.count_in_window(86400),
            }

    def reset(self, user_id: str) -> None:
        """Reset usage tracking for a user."""
        with self._lock:
            self._usage.pop(user_id, None)
            logger.info("quota_reset", user_id=user_id)
