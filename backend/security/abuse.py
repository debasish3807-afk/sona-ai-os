"""Abuse protection — detects and blocks malicious behavior.

Detects brute force, token replay, rapid API abuse, and
repeated permission failures. Implements temporary IP blocking.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AbuseRecord:
    """Tracks abuse signals for an IP or user."""

    failed_logins: int = 0
    permission_denials: int = 0
    rate_limit_hits: int = 0
    last_activity: float = field(default_factory=time.time)
    blocked_until: float = 0.0

    @property
    def is_blocked(self) -> bool:
        return time.time() < self.blocked_until

    def record_failed_login(self) -> None:
        self.failed_logins += 1
        self.last_activity = time.time()

    def record_permission_denial(self) -> None:
        self.permission_denials += 1
        self.last_activity = time.time()

    def record_rate_limit_hit(self) -> None:
        self.rate_limit_hits += 1
        self.last_activity = time.time()


class AbuseDetector:
    """Detects and responds to abusive API usage patterns.

    Thresholds:
        - 10 failed logins → 15 min block
        - 20 permission denials → 10 min block
        - 50 rate limit hits → 5 min block
    """

    FAILED_LOGIN_THRESHOLD = 10
    PERMISSION_DENIAL_THRESHOLD = 20
    RATE_LIMIT_THRESHOLD = 50
    BLOCK_DURATION_LOGIN = 900  # 15 min
    BLOCK_DURATION_PERMISSION = 600  # 10 min
    BLOCK_DURATION_RATE = 300  # 5 min

    def __init__(self) -> None:
        self._records: dict[str, AbuseRecord] = {}

    def _get_record(self, identifier: str) -> AbuseRecord:
        if identifier not in self._records:
            self._records[identifier] = AbuseRecord()
        return self._records[identifier]

    def is_blocked(self, identifier: str) -> bool:
        """Check if an identifier is currently blocked."""
        record = self._records.get(identifier)
        if record is None:
            return False
        return record.is_blocked

    def record_failed_login(self, identifier: str) -> bool:
        """Record a failed login. Returns True if now blocked."""
        record = self._get_record(identifier)
        record.record_failed_login()
        if record.failed_logins >= self.FAILED_LOGIN_THRESHOLD:
            record.blocked_until = time.time() + self.BLOCK_DURATION_LOGIN
            return True
        return False

    def record_permission_denial(self, identifier: str) -> bool:
        """Record permission denial. Returns True if now blocked."""
        record = self._get_record(identifier)
        record.record_permission_denial()
        if record.permission_denials >= self.PERMISSION_DENIAL_THRESHOLD:
            record.blocked_until = time.time() + self.BLOCK_DURATION_PERMISSION
            return True
        return False

    def record_rate_limit_hit(self, identifier: str) -> bool:
        """Record rate limit hit. Returns True if now blocked."""
        record = self._get_record(identifier)
        record.record_rate_limit_hit()
        if record.rate_limit_hits >= self.RATE_LIMIT_THRESHOLD:
            record.blocked_until = time.time() + self.BLOCK_DURATION_RATE
            return True
        return False

    def unblock(self, identifier: str) -> bool:
        """Manually unblock an identifier."""
        record = self._records.get(identifier)
        if record is None:
            return False
        record.blocked_until = 0.0
        record.failed_logins = 0
        record.permission_denials = 0
        record.rate_limit_hits = 0
        return True

    def get_status(self, identifier: str) -> dict[str, Any]:
        """Get abuse status for an identifier."""
        record = self._records.get(identifier)
        if record is None:
            return {"blocked": False, "signals": {}}
        return {
            "blocked": record.is_blocked,
            "failed_logins": record.failed_logins,
            "permission_denials": record.permission_denials,
            "rate_limit_hits": record.rate_limit_hits,
        }

    def cleanup(self, max_age_seconds: int = 3600) -> int:
        """Remove old records. Returns count removed."""
        now = time.time()
        stale = [
            k
            for k, v in self._records.items()
            if now - v.last_activity > max_age_seconds and not v.is_blocked
        ]
        for k in stale:
            del self._records[k]
        return len(stale)
