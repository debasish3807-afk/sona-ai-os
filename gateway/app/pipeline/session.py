"""Session management for tracking conversations.

Manages session lifecycle including creation, conversation ID mapping,
and session closure for the gateway pipeline.
"""

import uuid

import structlog

logger = structlog.get_logger()


class SessionManager:
    """Manages session state and conversation tracking.

    Maintains a mapping of session IDs to conversation IDs,
    allowing the pipeline to track multi-turn conversations.
    """

    def __init__(self) -> None:
        """Initialize the session manager with empty state."""
        self._sessions: dict[str, dict[str, str]] = {}

    def get_or_create_session(self, session_id: str | None, user_id: str) -> str:
        """Get an existing session or create a new one.

        Args:
            session_id: Optional existing session ID. If None, creates a new session.
            user_id: The user associated with the session.

        Returns:
            The session ID (existing or newly created).
        """
        if session_id and session_id in self._sessions:
            logger.debug(
                "session_reused",
                session_id=session_id,
                user_id=user_id,
            )
            return session_id

        new_session_id = session_id or str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        self._sessions[new_session_id] = {
            "user_id": user_id,
            "conversation_id": conversation_id,
        }

        logger.info(
            "session_created",
            session_id=new_session_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        return new_session_id

    def get_conversation_id(self, session_id: str) -> str:
        """Get the conversation ID for a session.

        Args:
            session_id: The session to look up.

        Returns:
            The conversation ID, or the session_id itself as fallback.
        """
        session = self._sessions.get(session_id)
        if session:
            return session["conversation_id"]
        return session_id

    def close_session(self, session_id: str) -> None:
        """Close and remove a session from tracking.

        Args:
            session_id: The session to close.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("session_closed", session_id=session_id)
