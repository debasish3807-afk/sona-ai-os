"""MCP Session Manager — tracks tool execution sessions.

Each session represents a connected client with its own execution
context, history, and permission scope.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class SessionStatus(str, Enum):
    """Session lifecycle states."""

    ACTIVE = "active"
    IDLE = "idle"
    CLOSED = "closed"


@dataclass
class MCPSession:
    """A single MCP client session.

    Tracks execution history, active tool calls, and session metadata.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    execution_count: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def record_execution(self, tool_name: str, success: bool, duration_ms: float) -> None:
        """Record a tool execution in session history."""
        self.execution_count += 1
        self.last_activity = datetime.now(UTC)
        self.history.append(
            {
                "tool": tool_name,
                "success": success,
                "duration_ms": round(duration_ms, 2),
                "timestamp": self.last_activity.isoformat(),
            }
        )
        # Keep only last 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]

    def close(self) -> None:
        """Mark session as closed."""
        self.status = SessionStatus.CLOSED

    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "execution_count": self.execution_count,
            "history_length": len(self.history),
        }


class MCPSessionManager:
    """Manages all active MCP sessions.

    Handles session creation, retrieval, and cleanup.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, MCPSession] = {}

    @property
    def active_count(self) -> int:
        """Number of active sessions."""
        return sum(1 for s in self._sessions.values() if s.status == SessionStatus.ACTIVE)

    def create_session(self, metadata: dict[str, Any] | None = None) -> MCPSession:
        """Create a new session.

        Args:
            metadata: Optional session metadata.

        Returns:
            The new MCPSession.
        """
        session = MCPSession(metadata=metadata or {})
        self._sessions[session.session_id] = session
        logger.debug("MCP session created", session_id=session.session_id)
        return session

    def get_session(self, session_id: str) -> MCPSession | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> MCPSession:
        """Get existing session or create a new one.

        Args:
            session_id: Optional session ID to look up.

        Returns:
            Existing or new MCPSession.
        """
        if session_id:
            existing = self._sessions.get(session_id)
            if existing and existing.status == SessionStatus.ACTIVE:
                return existing
        return self.create_session()

    def close_session(self, session_id: str) -> bool:
        """Close a session.

        Args:
            session_id: The session to close.

        Returns:
            True if session was found and closed.
        """
        session = self._sessions.get(session_id)
        if session:
            session.close()
            logger.debug("MCP session closed", session_id=session_id)
            return True
        return False

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions as dictionaries."""
        return [s.to_dict() for s in self._sessions.values()]

    def cleanup_stale(self, max_idle_seconds: int = 3600) -> int:
        """Remove sessions idle longer than threshold.

        Args:
            max_idle_seconds: Max idle time before cleanup.

        Returns:
            Number of sessions cleaned up.
        """
        now = datetime.now(UTC)
        stale_ids: list[str] = []
        for sid, session in self._sessions.items():
            if (
                session.status == SessionStatus.CLOSED
                or (now - session.last_activity).total_seconds() > max_idle_seconds
            ):
                stale_ids.append(sid)

        for sid in stale_ids:
            del self._sessions[sid]

        if stale_ids:
            logger.info("Cleaned stale MCP sessions", count=len(stale_ids))
        return len(stale_ids)
