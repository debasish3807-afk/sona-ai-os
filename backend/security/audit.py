"""Audit logging — records security-relevant events.

Tracks authentication, authorization, and administrative actions
with structured metadata for compliance and incident investigation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AuditAction(str, Enum):
    """Auditable security actions."""

    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_DENIED = "permission_denied"
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    TOOL_EXECUTION = "tool_execution"
    ADMIN_OPERATION = "admin_operation"
    DOCUMENT_UPLOAD = "document_upload"
    RATE_LIMITED = "rate_limited"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class AuditEvent:
    """A single audit log entry."""

    action: AuditAction
    user_id: str = ""
    username: str = ""
    ip_address: str = ""
    status: str = "success"  # success, failure, blocked
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "status": self.status,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class AuditLogger:
    """Records and retrieves audit events.

    Stores events in memory (production: use persistent backend).
    Emits structured log entries for each event.
    """

    def __init__(self, max_entries: int = 10000) -> None:
        self._events: list[AuditEvent] = []
        self._max_entries = max_entries

    def log(self, event: AuditEvent) -> None:
        """Record an audit event."""
        self._events.append(event)
        if len(self._events) > self._max_entries:
            self._events = self._events[-self._max_entries :]

        logger.info(
            "Audit event",
            action=event.action.value,
            user=event.username or event.user_id,
            ip=event.ip_address,
            status=event.status,
        )

    def log_action(
        self,
        action: AuditAction,
        user_id: str = "",
        username: str = "",
        ip_address: str = "",
        status: str = "success",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Convenience method to log an action."""
        event = AuditEvent(
            action=action,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            status=status,
            metadata=metadata or {},
        )
        self.log(event)

    def get_events(
        self,
        user_id: str | None = None,
        action: AuditAction | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve audit events with optional filters."""
        filtered = self._events
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        if action:
            filtered = [e for e in filtered if e.action == action]
        return [e.to_dict() for e in filtered[-limit:]]

    def get_failed_logins(self, ip_address: str, window_seconds: int = 300) -> int:
        """Count failed logins from an IP in a time window."""
        cutoff = datetime.now(UTC).isoformat()
        # Simple: count recent failed logins from this IP
        count = 0
        for event in reversed(self._events):
            if event.timestamp < cutoff:
                break
            if event.action == AuditAction.LOGIN_FAILED and event.ip_address == ip_address:
                count += 1
        return count

    @property
    def total_events(self) -> int:
        return len(self._events)
