"""Unit tests for SessionManager."""

import pytest

from sona_mcp.infrastructure.session_manager import SessionManager


class TestSessionCreation:
    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        mgr = SessionManager()
        session = await mgr.create_session("user-1")
        assert session.user_id == "user-1"
        assert session.session_id.startswith("session-")

    @pytest.mark.asyncio
    async def test_create_increments_count(self) -> None:
        mgr = SessionManager()
        await mgr.create_session("user-1")
        await mgr.create_session("user-2")
        assert mgr.active_session_count == 2

    @pytest.mark.asyncio
    async def test_create_replaces_existing(self) -> None:
        mgr = SessionManager()
        s1 = await mgr.create_session("user-1")
        s2 = await mgr.create_session("user-1")
        assert s1.session_id != s2.session_id
        assert mgr.active_session_count == 1

    @pytest.mark.asyncio
    async def test_session_initial_state(self) -> None:
        mgr = SessionManager()
        session = await mgr.create_session("user-1")
        assert session.active_calls == set()
        assert session.total_calls == 0


class TestSessionDestruction:
    @pytest.mark.asyncio
    async def test_destroy_existing(self) -> None:
        mgr = SessionManager()
        session = await mgr.create_session("user-1")
        result = await mgr.destroy_session(session.session_id)
        assert result is True
        assert mgr.active_session_count == 0

    @pytest.mark.asyncio
    async def test_destroy_nonexistent(self) -> None:
        mgr = SessionManager()
        result = await mgr.destroy_session("missing")
        assert result is False


class TestSessionLookup:
    @pytest.mark.asyncio
    async def test_get_session(self) -> None:
        mgr = SessionManager()
        created = await mgr.create_session("user-1")
        found = await mgr.get_session(created.session_id)
        assert found is not None
        assert found.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_get_session_missing(self) -> None:
        mgr = SessionManager()
        found = await mgr.get_session("nope")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_user_session(self) -> None:
        mgr = SessionManager()
        await mgr.create_session("user-1")
        found = await mgr.get_user_session("user-1")
        assert found is not None
        assert found.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_get_user_session_missing(self) -> None:
        mgr = SessionManager()
        found = await mgr.get_user_session("nobody")
        assert found is None


class TestSessionTracking:
    @pytest.mark.asyncio
    async def test_record_call_start(self) -> None:
        mgr = SessionManager()
        session = await mgr.create_session("user-1")
        result = await mgr.record_call_start(session.session_id, "tool_a")
        assert result is True
        assert "tool_a" in session.active_calls

    @pytest.mark.asyncio
    async def test_record_call_end(self) -> None:
        mgr = SessionManager()
        session = await mgr.create_session("user-1")
        await mgr.record_call_start(session.session_id, "tool_a")
        result = await mgr.record_call_end(session.session_id, "tool_a")
        assert result is True
        assert "tool_a" not in session.active_calls
        assert session.total_calls == 1

    @pytest.mark.asyncio
    async def test_record_on_missing_session(self) -> None:
        mgr = SessionManager()
        result = await mgr.record_call_start("missing", "tool_a")
        assert result is False

    @pytest.mark.asyncio
    async def test_multiple_active_calls(self) -> None:
        mgr = SessionManager()
        session = await mgr.create_session("user-1")
        await mgr.record_call_start(session.session_id, "t1")
        await mgr.record_call_start(session.session_id, "t2")
        assert len(session.active_calls) == 2


class TestSessionCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_expired(self) -> None:
        mgr = SessionManager(session_timeout=0.0)  # Instant timeout
        await mgr.create_session("user-1")
        cleaned = await mgr.cleanup_expired()
        assert cleaned == 1
        assert mgr.active_session_count == 0

    @pytest.mark.asyncio
    async def test_cleanup_no_expired(self) -> None:
        mgr = SessionManager(session_timeout=3600.0)
        await mgr.create_session("user-1")
        cleaned = await mgr.cleanup_expired()
        assert cleaned == 0
        assert mgr.active_session_count == 1


class TestSessionList:
    @pytest.mark.asyncio
    async def test_list_sessions(self) -> None:
        mgr = SessionManager()
        await mgr.create_session("user-1")
        await mgr.create_session("user-2")
        sessions = await mgr.list_sessions()
        assert len(sessions) == 2
