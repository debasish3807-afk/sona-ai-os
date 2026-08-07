"""Audit logger for security events.

Provides structured audit logging with queryable trail, retention policies,
and event categorization.
"""

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger()


class AuditEventType(StrEnum):
    """Types of audit events."""

    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    SAFETY_CHECK_PASS = "safety_check_pass"
    SAFETY_CHECK_FAIL = "safety_check_fail"
    RATE_LIMIT_HIT = "rate_limit_hit"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    TOOL_ACCESS = "tool_access"
    TOOL_DENIED = "tool_denied"


@dataclass
class AuditEntry:
    """A single audit log entry."""

    event_type: str
    timestamp: float
    user_id: str = ""
    resource: str = ""
    action: str = ""
    outcome: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    session_id: str = ""


class AuditLogger:
    """Structured audit logger with queryable trail."""

    def __init__(self, max_entries: int = 10000, retention_hours: int = 720) -> None:
        self._entries: list[AuditEntry] = []
        self._max_entries = max_entries
        self._retention_seconds = retention_hours * 3600

    @property
    def entries(self) -> list[AuditEntry]:
        """Access all audit entries."""
        return self._entries

    async def log(
        self,
        event_type: str,
        user_id: str = "",
        resource: str = "",
        action: str = "",
        outcome: str = "",
        details: dict[str, Any] | None = None,
        ip_address: str = "",
        session_id: str = "",
    ) -> AuditEntry:
        """Record an audit log entry."""
        entry = AuditEntry(
            event_type=event_type,
            timestamp=time.time(),
            user_id=user_id,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id,
        )
        self._entries.append(entry)

        # Enforce max entries
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries :]

        logger.info(
            "audit_event",
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            outcome=outcome,
        )
        return entry

    async def query(
        self,
        event_type: str | None = None,
        user_id: str | None = None,
        resource: str | None = None,
        since: float | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query audit entries with optional filters."""
        results: list[AuditEntry] = []
        for entry in reversed(self._entries):
            if event_type and entry.event_type != event_type:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if resource and entry.resource != resource:
                continue
            if since and entry.timestamp < since:
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    async def count_by_type(self, event_type: str, since: float | None = None) -> int:
        """Count entries of a specific type."""
        count = 0
        for entry in self._entries:
            if entry.event_type == event_type:
                if since is None or entry.timestamp >= since:
                    count += 1
        return count

    async def cleanup(self) -> int:
        """Remove entries older than retention period.

        Returns:
            Number of entries removed.
        """
        cutoff = time.time() - self._retention_seconds
        original_count = len(self._entries)
        self._entries = [e for e in self._entries if e.timestamp >= cutoff]
        removed = original_count - len(self._entries)
        if removed > 0:
            logger.info("audit_cleanup", removed=removed)
        return removed

    async def clear(self) -> None:
        """Clear all audit entries."""
        self._entries.clear()
