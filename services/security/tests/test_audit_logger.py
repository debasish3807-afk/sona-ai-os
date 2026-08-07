"""Tests for the audit logger."""

import time

import pytest

from sona_security.infrastructure.audit_logger import AuditEventType, AuditLogger


class TestAuditLogger:
    def setup_method(self) -> None:
        self.logger = AuditLogger(max_entries=100)

    @pytest.mark.asyncio
    async def test_log_entry(self) -> None:
        entry = await self.logger.log(
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id="user-1",
        )
        assert entry.event_type == AuditEventType.AUTH_SUCCESS
        assert entry.user_id == "user-1"
        assert entry.timestamp > 0

    @pytest.mark.asyncio
    async def test_log_with_details(self) -> None:
        entry = await self.logger.log(
            event_type=AuditEventType.AUTH_FAILURE,
            user_id="user-1",
            details={"reason": "bad_password"},
        )
        assert entry.details["reason"] == "bad_password"

    @pytest.mark.asyncio
    async def test_log_with_resource(self) -> None:
        entry = await self.logger.log(
            event_type=AuditEventType.PERMISSION_DENIED,
            user_id="user-1",
            resource="agents",
            action="delete",
        )
        assert entry.resource == "agents"
        assert entry.action == "delete"

    @pytest.mark.asyncio
    async def test_entries_list(self) -> None:
        await self.logger.log(event_type="test1")
        await self.logger.log(event_type="test2")
        assert len(self.logger.entries) == 2

    @pytest.mark.asyncio
    async def test_max_entries_enforced(self) -> None:
        logger = AuditLogger(max_entries=5)
        for i in range(10):
            await logger.log(event_type=f"event-{i}")
        assert len(logger.entries) == 5

    @pytest.mark.asyncio
    async def test_query_by_event_type(self) -> None:
        await self.logger.log(event_type="auth_success", user_id="u1")
        await self.logger.log(event_type="auth_failure", user_id="u2")
        await self.logger.log(event_type="auth_success", user_id="u3")
        results = await self.logger.query(event_type="auth_success")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_by_user_id(self) -> None:
        await self.logger.log(event_type="test", user_id="user-1")
        await self.logger.log(event_type="test", user_id="user-2")
        results = await self.logger.query(user_id="user-1")
        assert len(results) == 1
        assert results[0].user_id == "user-1"

    @pytest.mark.asyncio
    async def test_query_by_resource(self) -> None:
        await self.logger.log(event_type="test", resource="agents")
        await self.logger.log(event_type="test", resource="memory")
        results = await self.logger.query(resource="agents")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_query_with_limit(self) -> None:
        for i in range(20):
            await self.logger.log(event_type="test", user_id=f"user-{i}")
        results = await self.logger.query(limit=5)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_query_since_timestamp(self) -> None:
        await self.logger.log(event_type="old")
        cutoff = time.time()
        await self.logger.log(event_type="new")
        results = await self.logger.query(since=cutoff)
        assert len(results) == 1
        assert results[0].event_type == "new"

    @pytest.mark.asyncio
    async def test_count_by_type(self) -> None:
        await self.logger.log(event_type="auth_success")
        await self.logger.log(event_type="auth_success")
        await self.logger.log(event_type="auth_failure")
        count = await self.logger.count_by_type("auth_success")
        assert count == 2

    @pytest.mark.asyncio
    async def test_cleanup(self) -> None:
        logger = AuditLogger(retention_hours=0)  # Immediate expiry
        await logger.log(event_type="old")
        # Small sleep to ensure timestamp difference
        import asyncio

        await asyncio.sleep(0.01)
        removed = await logger.cleanup()
        assert removed == 1
        assert len(logger.entries) == 0

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        await self.logger.log(event_type="test")
        await self.logger.log(event_type="test")
        await self.logger.clear()
        assert len(self.logger.entries) == 0

    @pytest.mark.asyncio
    async def test_audit_event_types(self) -> None:
        assert AuditEventType.AUTH_SUCCESS == "auth_success"
        assert AuditEventType.PERMISSION_DENIED == "permission_denied"
        assert AuditEventType.RATE_LIMIT_HIT == "rate_limit_hit"
