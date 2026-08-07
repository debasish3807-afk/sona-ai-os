"""Session management for MCP Integration.

Manages per-user MCP sessions with tracking of active tool calls,
session timeouts, cleanup, and resource isolation.
"""

import time
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class MCPSession:
    """Represents an active MCP session for a user.

    Attributes:
        session_id: Unique identifier for this session.
        user_id: The user who owns this session.
        created_at: Timestamp when the session was created.
        last_activity: Timestamp of the last activity.
        active_calls: Set of tool names currently being called.
        total_calls: Total number of tool calls in this session.
    """

    session_id: str
    user_id: str
    created_at: float = field(default_factory=time.monotonic)
    last_activity: float = field(default_factory=time.monotonic)
    active_calls: set[str] = field(default_factory=set)
    total_calls: int = 0


class SessionManager:
    """Manages MCP sessions with lifecycle, tracking, and cleanup.

    Provides session creation, destruction, activity tracking,
    timeout handling, and resource isolation between sessions.
    """

    def __init__(self, session_timeout: float = 3600.0) -> None:
        """Initialize the session manager.

        Args:
            session_timeout: Session inactivity timeout in seconds.
        """
        self._sessions: dict[str, MCPSession] = {}
        self._user_sessions: dict[str, str] = {}  # user_id -> session_id
        self._session_timeout = session_timeout
        self._next_id = 0

    async def create_session(self, user_id: str) -> MCPSession:
        """Create a new session for a user.

        If the user already has an active session, it is destroyed first.

        Args:
            user_id: The user to create a session for.

        Returns:
            The newly created MCPSession.
        """
        # Destroy existing session for this user
        if user_id in self._user_sessions:
            await self.destroy_session(self._user_sessions[user_id])

        self._next_id += 1
        session_id = f"session-{self._next_id}"
        session = MCPSession(session_id=session_id, user_id=user_id)
        self._sessions[session_id] = session
        self._user_sessions[user_id] = session_id

        await logger.ainfo("session_created", session_id=session_id, user_id=user_id)
        return session

    async def destroy_session(self, session_id: str) -> bool:
        """Destroy a session and clean up resources.

        Args:
            session_id: The session to destroy.

        Returns:
            True if the session was destroyed, False if not found.
        """
        session = self._sessions.pop(session_id, None)
        if session is None:
            return False

        self._user_sessions.pop(session.user_id, None)
        await logger.ainfo(
            "session_destroyed",
            session_id=session_id,
            user_id=session.user_id,
            total_calls=session.total_calls,
        )
        return True

    async def get_session(self, session_id: str) -> MCPSession | None:
        """Get a session by its ID.

        Args:
            session_id: The session identifier.

        Returns:
            The MCPSession if found, None otherwise.
        """
        return self._sessions.get(session_id)

    async def get_user_session(self, user_id: str) -> MCPSession | None:
        """Get the active session for a user.

        Args:
            user_id: The user identifier.

        Returns:
            The user's MCPSession if one exists, None otherwise.
        """
        session_id = self._user_sessions.get(user_id)
        if session_id is None:
            return None
        return self._sessions.get(session_id)

    async def record_call_start(self, session_id: str, tool_name: str) -> bool:
        """Record that a tool call has started in a session.

        Args:
            session_id: The session identifier.
            tool_name: The tool being called.

        Returns:
            True if recorded, False if session not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session.active_calls.add(tool_name)
        session.last_activity = time.monotonic()
        return True

    async def record_call_end(self, session_id: str, tool_name: str) -> bool:
        """Record that a tool call has completed in a session.

        Args:
            session_id: The session identifier.
            tool_name: The tool that completed.

        Returns:
            True if recorded, False if session not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session.active_calls.discard(tool_name)
        session.total_calls += 1
        session.last_activity = time.monotonic()
        return True

    async def cleanup_expired(self) -> int:
        """Remove all sessions that have exceeded the timeout.

        Returns:
            The number of sessions that were cleaned up.
        """
        now = time.monotonic()
        expired: list[str] = []

        for session_id, session in self._sessions.items():
            if now - session.last_activity > self._session_timeout:
                expired.append(session_id)

        for session_id in expired:
            await self.destroy_session(session_id)

        if expired:
            await logger.ainfo("sessions_cleaned_up", count=len(expired))
        return len(expired)

    @property
    def active_session_count(self) -> int:
        """Return the number of active sessions."""
        return len(self._sessions)

    async def list_sessions(self) -> list[MCPSession]:
        """List all active sessions.

        Returns:
            A list of all active MCPSession instances.
        """
        return list(self._sessions.values())
