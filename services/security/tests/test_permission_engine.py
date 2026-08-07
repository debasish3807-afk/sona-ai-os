"""Tests for the permission engine."""

import pytest

from sona_security.domain.models import Permission, Role
from sona_security.infrastructure.permission_engine import (
    PermissionEngine,
    PolicyContext,
)


class TestPermissionEngine:
    def setup_method(self) -> None:
        self.engine = PermissionEngine()

    @pytest.mark.asyncio
    async def test_admin_always_allowed(self) -> None:
        perm = Permission(resource="anything", action="anything")
        ctx = PolicyContext(user_id="admin-1")
        result = await self.engine.evaluate(perm, [Role.ADMIN], ctx)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_user_read_allowed(self) -> None:
        perm = Permission(resource="agents", action="read")
        ctx = PolicyContext(user_id="user-1")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_user_write_allowed(self) -> None:
        perm = Permission(resource="agents", action="write")
        ctx = PolicyContext(user_id="user-1")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_user_delete_denied(self) -> None:
        perm = Permission(resource="agents", action="delete")
        ctx = PolicyContext(user_id="user-1")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_readonly_read_allowed(self) -> None:
        perm = Permission(resource="agents", action="read")
        ctx = PolicyContext(user_id="reader-1")
        result = await self.engine.evaluate(perm, [Role.READONLY], ctx)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_readonly_write_denied(self) -> None:
        perm = Permission(resource="agents", action="write")
        ctx = PolicyContext(user_id="reader-1")
        result = await self.engine.evaluate(perm, [Role.READONLY], ctx)
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_service_execute_allowed(self) -> None:
        perm = Permission(resource="tools", action="execute")
        ctx = PolicyContext(user_id="svc-1")
        result = await self.engine.evaluate(perm, [Role.SERVICE], ctx)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_no_roles_denied(self) -> None:
        perm = Permission(resource="agents", action="read")
        ctx = PolicyContext(user_id="user-1")
        result = await self.engine.evaluate(perm, [], ctx)
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_owner_only_condition_allowed(self) -> None:
        perm = Permission(resource="agents", action="read", conditions={"owner_only": True})
        ctx = PolicyContext(user_id="user-1", resource_owner_id="user-1")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_owner_only_condition_denied(self) -> None:
        perm = Permission(resource="agents", action="read", conditions={"owner_only": True})
        ctx = PolicyContext(user_id="user-1", resource_owner_id="user-2")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_custom_deny_policy(self) -> None:
        self.engine.add_policy(
            {
                "name": "deny_delete",
                "resource": "agents",
                "action": "delete",
                "effect": "deny",
            }
        )
        perm = Permission(resource="agents", action="delete")
        ctx = PolicyContext(user_id="admin-1")
        result = await self.engine.evaluate(perm, [Role.ADMIN], ctx)
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_custom_allow_policy(self) -> None:
        self.engine.add_policy(
            {
                "name": "allow_all",
                "resource": "*",
                "action": "*",
                "effect": "allow",
            }
        )
        perm = Permission(resource="agents", action="read")
        ctx = PolicyContext(user_id="user-1")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_result_has_conditions_met(self) -> None:
        perm = Permission(resource="agents", action="read")
        ctx = PolicyContext(user_id="user-1")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert "role_check" in result.conditions_met

    @pytest.mark.asyncio
    async def test_time_window_condition(self) -> None:
        perm = Permission(
            resource="agents",
            action="read",
            conditions={"time_window": {"start": "09:00", "end": "17:00"}},
        )
        ctx = PolicyContext(user_id="user-1", timestamp="2025-01-01T12:00:00Z")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_time_window_outside(self) -> None:
        perm = Permission(
            resource="agents",
            action="read",
            conditions={"time_window": {"start": "09:00", "end": "17:00"}},
        )
        ctx = PolicyContext(user_id="user-1", timestamp="2025-01-01T22:00:00Z")
        result = await self.engine.evaluate(perm, [Role.USER], ctx)
        assert result.allowed is False
