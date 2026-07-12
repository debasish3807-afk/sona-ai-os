"""Session management — active sessions, device tracking, expiration.

Tracks authenticated sessions with device and IP metadata.
Supports logout from all devices and session revocation.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", "3600"))


@dataclass
class Session:
    """An active user session."""

    session_id: str = field(default_factory=lambda: secrets.token_hex(16))
    user_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    device: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    expires_at: str = field(
        default_factory=lambda: (datetime.now(UTC) + timedelta(seconds=SESSION_TIMEOUT)).isoformat()
    )
    is_active: bool = True

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC).isoformat() > self.expires_at

    def refresh(self) -> None:
        """Extend session expiration."""
        self.last_activity = datetime.now(UTC).isoformat()
        self.expires_at = (datetime.now(UTC) + timedelta(seconds=SESSION_TIMEOUT)).isoformat()

    def revoke(self) -> None:
        """Revoke this session."""
        self.is_active = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device": self.device,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
        }


class SessionManager:
    """Manages active user sessions with device tracking."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._user_sessions: dict[str, list[str]] = {}  # user_id → [session_ids]

    def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
        device: str = "",
    ) -> Session:
        """Create a new session for a user."""
        session = Session(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device=device or self._detect_device(user_agent),
        )
        self._sessions[session.session_id] = session
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session.session_id)
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if not session.is_active or session.is_expired:
            return None
        return session

    def refresh_session(self, session_id: str) -> bool:
        """Refresh a session's expiration."""
        session = self.get_session(session_id)
        if session is None:
            return False
        session.refresh()
        return True

    def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session."""
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session.revoke()
        return True

    def revoke_all_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user (logout all devices)."""
        session_ids = self._user_sessions.get(user_id, [])
        count = 0
        for sid in session_ids:
            session = self._sessions.get(sid)
            if session and session.is_active:
                session.revoke()
                count += 1
        return count

    def list_sessions(self, user_id: str) -> list[dict[str, Any]]:
        """List active sessions for a user."""
        session_ids = self._user_sessions.get(user_id, [])
        result: list[dict[str, Any]] = []
        for sid in session_ids:
            session = self._sessions.get(sid)
            if session and session.is_active and not session.is_expired:
                result.append(session.to_dict())
        return result

    def get_active_count(self, user_id: str) -> int:
        """Count active sessions for a user."""
        return len(self.list_sessions(user_id))

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        expired: list[str] = []
        for sid, session in self._sessions.items():
            if session.is_expired or not session.is_active:
                expired.append(sid)
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def _detect_device(self, user_agent: str) -> str:
        """Simple device detection from user agent."""
        ua = user_agent.lower()
        if "mobile" in ua or "android" in ua or "iphone" in ua:
            return "mobile"
        if "tablet" in ua or "ipad" in ua:
            return "tablet"
        return "desktop"
