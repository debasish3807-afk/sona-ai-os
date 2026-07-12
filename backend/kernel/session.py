"""Session management for AI kernel.

Manages the lifecycle of user interaction sessions including creation,
state tracking, history management, and cleanup.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class SessionStatus(str, Enum):
    """Status of a kernel session."""

    ACTIVE = "active"
    IDLE = "idle"
    PROCESSING = "processing"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass
class SessionConfig:
    """Configuration for a new session.

    Attributes:
        max_idle_seconds: Maximum idle time before session expires.
        max_history_length: Maximum messages to retain in history.
        model_preference: Preferred model for this session.
        system_prompt_id: Optional custom system prompt identifier.
        features: Enabled feature flags for this session.
        metadata: Additional session configuration.
    """

    max_idle_seconds: int = 3600
    max_history_length: int = 100
    model_preference: Optional[str] = None
    system_prompt_id: Optional[str] = None
    features: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMessage:
    """A message within a session's conversation history.

    Attributes:
        message_id: Unique message identifier.
        role: Message role (user, assistant, system, tool).
        content: Message content.
        timestamp: When the message was created.
        model_used: Which model generated this (for assistant messages).
        token_count: Token count for this message.
        metadata: Additional message metadata.
    """

    role: str
    content: str
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model_used: Optional[str] = None
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """Represents an active kernel session.

    Attributes:
        session_id: Unique session identifier.
        user_id: Identifier of the session owner.
        status: Current session status.
        config: Session configuration.
        messages: Conversation history.
        created_at: Session creation timestamp.
        updated_at: Last activity timestamp.
        total_tokens_used: Cumulative token usage.
        total_requests: Number of requests processed.
        metadata: Additional session data.
    """

    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid4()))
    status: SessionStatus = SessionStatus.ACTIVE
    config: SessionConfig = field(default_factory=SessionConfig)
    messages: List[SessionMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_tokens_used: int = 0
    total_requests: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if the session is in an active state."""
        return self.status in (SessionStatus.ACTIVE, SessionStatus.PROCESSING)

    @property
    def message_count(self) -> int:
        """Get the number of messages in the session."""
        return len(self.messages)


@dataclass
class SessionSummary:
    """Lightweight session summary for listing.

    Attributes:
        session_id: Session identifier.
        user_id: Owner identifier.
        status: Current status.
        message_count: Number of messages.
        created_at: Creation timestamp.
        updated_at: Last activity timestamp.
    """

    session_id: str
    user_id: str
    status: SessionStatus
    message_count: int
    created_at: datetime
    updated_at: datetime


class SessionManager(ABC):
    """Abstract interface for session management.

    Handles the full lifecycle of user sessions including creation,
    message management, state transitions, and cleanup.
    """

    @abstractmethod
    async def create_session(
        self,
        user_id: str,
        config: Optional[SessionConfig] = None,
    ) -> Session:
        """Create a new session for a user.

        Args:
            user_id: Identifier of the session owner.
            config: Optional session configuration.

        Returns:
            Newly created Session instance.
        """
        ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID.

        Args:
            session_id: The session identifier.

        Returns:
            Session instance or None if not found.
        """
        ...

    @abstractmethod
    async def update_session(
        self,
        session_id: str,
        status: Optional[SessionStatus] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Session]:
        """Update session status or metadata.

        Args:
            session_id: The session to update.
            status: Optional new status.
            metadata: Optional metadata updates (merged with existing).

        Returns:
            Updated Session or None if not found.
        """
        ...

    @abstractmethod
    async def close_session(self, session_id: str) -> bool:
        """Close a session and perform cleanup.

        Args:
            session_id: The session to close.

        Returns:
            True if the session was found and closed.
        """
        ...

    @abstractmethod
    async def add_message(
        self,
        session_id: str,
        message: SessionMessage,
    ) -> None:
        """Add a message to a session's history.

        Args:
            session_id: Target session.
            message: The message to add.

        Raises:
            ValueError: If the session is not found or not active.
        """
        ...

    @abstractmethod
    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[SessionMessage]:
        """Retrieve messages from a session's history.

        Args:
            session_id: The session to query.
            limit: Maximum number of messages to return.
            offset: Number of messages to skip from the start.

        Returns:
            List of SessionMessage instances.
        """
        ...

    @abstractmethod
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SessionSummary]:
        """List sessions with optional filtering.

        Args:
            user_id: Optional filter by owner.
            status: Optional filter by status.
            limit: Maximum sessions to return.
            offset: Number of sessions to skip.

        Returns:
            List of SessionSummary instances.
        """
        ...

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired and idle sessions.

        Returns:
            Number of sessions cleaned up.
        """
        ...
