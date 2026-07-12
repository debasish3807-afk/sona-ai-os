"""Rate limiting — sliding window algorithm with per-endpoint limits.

Provides IP-based and user-based rate limiting with configurable
limits per endpoint category. Returns HTTP 429 with Retry-After header.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"


@dataclass
class RateLimit:
    """Rate limit configuration for an endpoint category."""

    requests: int
    window_seconds: int = 60


# Default limits per endpoint category
DEFAULT_LIMITS: dict[str, RateLimit] = {
    "login": RateLimit(requests=5, window_seconds=60),
    "register": RateLimit(requests=3, window_seconds=60),
    "chat": RateLimit(requests=60, window_seconds=60),
    "tools": RateLimit(requests=30, window_seconds=60),
    "documents": RateLimit(requests=20, window_seconds=60),
    "admin": RateLimit(requests=100, window_seconds=60),
    "default": RateLimit(requests=120, window_seconds=60),
}


class RateLimiter:
    """Sliding window rate limiter.

    Tracks request timestamps per key (IP or user ID) and category.
    Rejects requests exceeding the configured limit within the window.
    """

    def __init__(self, limits: dict[str, RateLimit] | None = None) -> None:
        self._limits = limits or DEFAULT_LIMITS
        self._windows: dict[str, list[float]] = {}

    @property
    def enabled(self) -> bool:
        return RATE_LIMIT_ENABLED

    def _get_key(self, identifier: str, category: str) -> str:
        return f"{category}:{identifier}"

    def _get_limit(self, category: str) -> RateLimit:
        return self._limits.get(category, self._limits["default"])

    def check(self, identifier: str, category: str = "default") -> tuple[bool, dict[str, Any]]:
        """Check if a request is allowed under rate limits.

        Args:
            identifier: IP address or user ID.
            category: Endpoint category (login, chat, tools, etc.).

        Returns:
            Tuple of (allowed: bool, headers: dict with limit info).
        """
        if not self.enabled:
            return True, {}

        key = self._get_key(identifier, category)
        limit = self._get_limit(category)
        now = time.time()
        window_start = now - limit.window_seconds

        # Get or create window
        if key not in self._windows:
            self._windows[key] = []

        # Remove expired entries (sliding window)
        self._windows[key] = [t for t in self._windows[key] if t > window_start]

        current_count = len(self._windows[key])
        remaining = max(0, limit.requests - current_count)

        headers = {
            "X-RateLimit-Limit": str(limit.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(window_start + limit.window_seconds)),
        }

        if current_count >= limit.requests:
            # Calculate retry-after
            oldest = self._windows[key][0] if self._windows[key] else now
            retry_after = int(oldest + limit.window_seconds - now) + 1
            headers["Retry-After"] = str(max(1, retry_after))
            return False, headers

        # Allow and record
        self._windows[key].append(now)
        return True, headers

    def record(self, identifier: str, category: str = "default") -> None:
        """Record a request without checking (for pre-validated requests)."""
        key = self._get_key(identifier, category)
        if key not in self._windows:
            self._windows[key] = []
        self._windows[key].append(time.time())

    def get_remaining(self, identifier: str, category: str = "default") -> int:
        """Get remaining requests for an identifier."""
        key = self._get_key(identifier, category)
        limit = self._get_limit(category)
        now = time.time()
        window_start = now - limit.window_seconds

        entries = self._windows.get(key, [])
        current = sum(1 for t in entries if t > window_start)
        return max(0, limit.requests - current)

    def reset(self, identifier: str, category: str | None = None) -> None:
        """Reset rate limit for an identifier."""
        if category:
            key = self._get_key(identifier, category)
            self._windows.pop(key, None)
        else:
            # Reset all categories for this identifier
            keys_to_remove = [
                k
                for k in self._windows
                if k.endswith(f":{identifier}") or k.startswith(f"{identifier}:") or identifier in k
            ]
            for k in keys_to_remove:
                del self._windows[k]

    def cleanup(self) -> int:
        """Remove expired window entries. Returns entries cleaned."""
        now = time.time()
        max_window = max(lim.window_seconds for lim in self._limits.values())
        cutoff = now - max_window
        cleaned = 0
        empty_keys: list[str] = []

        for key, timestamps in self._windows.items():
            before = len(timestamps)
            self._windows[key] = [t for t in timestamps if t > cutoff]
            cleaned += before - len(self._windows[key])
            if not self._windows[key]:
                empty_keys.append(key)

        for k in empty_keys:
            del self._windows[k]

        return cleaned
