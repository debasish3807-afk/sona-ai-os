"""Tests for session management."""

import pytest

from app.pipeline.session import SessionManager


class TestSessionManager:
    """Tests for the SessionManager class."""

    @pytest.fixture
    def manager(self) -> SessionManager:
        """Create a fresh SessionManager for each test."""
        return SessionManager()

    def test_create_new_session_no_id(self, manager: SessionManager) -> None:
        """Creating a session without an ID generates a new UUID."""
        session_id = manager.get_or_create_session(None, "user-1")
        assert session_id is not None
        assert len(session_id) > 0

    def test_create_new_session_with_id(self, manager: SessionManager) -> None:
        """Creating a session with an explicit ID uses that ID."""
        session_id = manager.get_or_create_session("my-session", "user-1")
        assert session_id == "my-session"

    def test_reuse_existing_session(self, manager: SessionManager) -> None:
        """Getting an existing session returns the same ID."""
        first = manager.get_or_create_session("sess-1", "user-1")
        second = manager.get_or_create_session("sess-1", "user-1")
        assert first == second

    def test_different_users_different_sessions(self, manager: SessionManager) -> None:
        """Different session IDs can be created for different users."""
        s1 = manager.get_or_create_session(None, "user-1")
        s2 = manager.get_or_create_session(None, "user-2")
        assert s1 != s2

    def test_get_conversation_id(self, manager: SessionManager) -> None:
        """Conversation ID is returned for an existing session."""
        manager.get_or_create_session("sess-1", "user-1")
        conv_id = manager.get_conversation_id("sess-1")
        assert conv_id is not None
        assert len(conv_id) > 0

    def test_get_conversation_id_unknown_session(self, manager: SessionManager) -> None:
        """Unknown session returns the session_id itself as fallback."""
        conv_id = manager.get_conversation_id("unknown-session")
        assert conv_id == "unknown-session"

    def test_close_session(self, manager: SessionManager) -> None:
        """Closing a session removes it from tracking."""
        manager.get_or_create_session("sess-1", "user-1")
        manager.close_session("sess-1")
        # After closing, it should create a new session
        conv_id = manager.get_conversation_id("sess-1")
        assert conv_id == "sess-1"  # Falls back since session was removed

    def test_close_nonexistent_session(self, manager: SessionManager) -> None:
        """Closing a non-existent session does not raise."""
        manager.close_session("does-not-exist")  # Should not raise
