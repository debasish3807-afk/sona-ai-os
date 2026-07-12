"""Session memory - per-session state management.

This module defines the session memory interface for managing per-session
state including active context, session lifecycle, and session-scoped
memory entries. Sessions are the boundary for working memory isolation.

Classes:
    SessionMemoryConfig: Configuration for session memory behavior.
    SessionState: State data for a single session.
    SessionMemory: Abstract interface for session memory operations.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SessionMemoryConfig:
    """Configuration for session memory behavior.

    Controls session limits, timeout behavior, and summarization on close.

    Attributes:
        max_sessions: Maximum number of concurrent active sessions.
        session_timeout_seconds: Seconds of inactivity before session expires.
        auto_summarize_on_close: Whether to generate a summary when session closes.
        preserve_context_on_close: Whether to save context to short-term on close.
        max_entries_per_session: Maximum entries per session.
    """

    max_sessions: int = 100
    session_timeout_seconds: int = 3600
    auto_summarize_on_close: bool = True
    preserve_context_on_close: bool = True
    max_entries_per_session: int = 500


@dataclass(slots=True)
class SessionState:
    """State data for a single session.

    Captures the complete state of an active session including identity,
    timing, entries, and associated working memory.

    Attributes:
        session_id: Unique identifier for this session (UUID4).
        user_id: ID of the user who owns this session.
        started_at: UTC timestamp when the session was created.
        last_active: UTC timestamp of the most recent activity.
        entries: List of memory entry IDs stored in this session.
        working_memory_ids: IDs of entries currently in working memory.
        active: Whether this session is currently active.
        summary: Optional summary generated on session close.
        metadata: Additional session metadata (e.g., client info, preferences).
    """

    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_active: datetime = field(default_factory=lambda: datetime.now(UTC))
    entries: list[str] = field(default_factory=list)
    working_memory_ids: list[str] = field(default_factory=list)
    active: bool = True
    summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionMemory(ABC):
    """Abstract interface for session memory operations.

    Manages session lifecycle including creation, state tracking,
    updates, closure, and cleanup of expired sessions.
    """

    @abstractmethod
    async def create_session(self, user_id: str, metadata: dict[str, Any] | None = None) -> str:
        """Create a new session for a user.

        Args:
            user_id: The user ID to create the session for.
            metadata: Optional initial session metadata.

        Returns:
            The session_id of the created session.
        """
        ...

    @abstractmethod
    async def get_session(self, session_id: str) -> SessionState | None:
        """Retrieve session state by session ID.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            The session state if found, None otherwise.
        """
        ...

    @abstractmethod
    async def update_session(
        self,
        session_id: str,
        entries: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update session state with new entries or metadata.

        Updates the last_active timestamp automatically.

        Args:
            session_id: The session to update.
            entries: Optional new entry IDs to add to the session.
            metadata: Optional metadata to merge into session metadata.
        """
        ...

    @abstractmethod
    async def close_session(self, session_id: str) -> None:
        """Close a session gracefully.

        Marks the session as inactive. If auto_summarize_on_close is
        enabled, generates a summary. If preserve_context_on_close is
        enabled, migrates context to short-term memory.

        Args:
            session_id: The session to close.
        """
        ...

    @abstractmethod
    async def get_active_sessions(self, user_id: str) -> list[SessionState]:
        """Get all active sessions for a user.

        Args:
            user_id: The user ID to get sessions for.

        Returns:
            List of active session states for the user.
        """
        ...

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions.

        Identifies sessions that have exceeded their timeout and
        closes them. This includes summarization if configured.

        Returns:
            Number of sessions that were cleaned up.
        """
        ...
