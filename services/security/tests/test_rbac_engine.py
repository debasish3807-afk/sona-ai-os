"""Tests for the RBAC engine."""

import pytest

from sona_security.application.ports import AuthorizationPort
from sona_security.domain.models import Permission, Role
from sona_security.infrastructure.rbac_engine import RBACEngine


class TestRBACEngine:
    def setup_method(self) -> None:
        self.rbac = RBACEngine()

    @pytest.mark.asyncio
    async def test_implements_authorization_port(self) -> None:
        assert isinstance(self.rbac, AuthorizationPort)

    @pytest.mark.asyncio
    async def test_assign_role(self) -> None:
        result = await self.rbac.assign_role("user-1", Role.USER)
        assert result is True
        roles = await self.rbac.get_user_roles("user-1")
        assert Role.USER in roles

    @pytest.mark.asyncio
    async def test_assign_multiple_roles(self) -> None:
        await self.rbac.assign_role("user-1", Role.USER)
        await self.rbac.assign_role("user-1", Role.ADMIN)
        roles = await self.rbac.get_user_roles("user-1")
        assert Role.USER in roles
        assert Role.ADMIN in roles

    @pytest.mark.asyncio
    async def test_assign_duplicate_role(self) -> None:
        await self.rbac.assign_role("user-1", Role.USER)
        await self.rbac.assign_role("user-1", Role.USER)
        roles = await self.rbac.get_user_roles("user-1")
        assert roles.count(Role.USER) == 1

    @pytest.mark.asyncio
    async def test_remove_role(self) -> None:
        await self.rbac.assign_role("user-1", Role.USER)
        await self.rbac.assign_role("user-1", Role.ADMIN)
        result = await self.rbac.remove_role("user-1", Role.ADMIN)
        assert result is True
        roles = await self.rbac.get_user_roles("user-1")
        assert Role.ADMIN not in roles

    @pytest.mark.asyncio
    async def test_remove_nonexistent_role(self) -> None:
        await self.rbac.assign_role("user-1", Role.USER)
        result = await self.rbac.remove_role("user-1", Role.ADMIN)
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_role_unknown_user(self) -> None:
        result = await self.rbac.remove_role("unknown", Role.USER)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_roles_empty(self) -> None:
        roles = await self.rbac.get_user_roles("no-roles-user")
        assert roles == []

    @pytest.mark.asyncio
    async def test_admin_has_all_permissions(self) -> None:
        await self.rbac.assign_role("admin-1", Role.ADMIN)
        perm = Permission(resource="agents", action="delete")
        assert await self.rbac.check_permission("admin-1", perm) is True

    @pytest.mark.asyncio
    async def test_admin_any_resource(self) -> None:
        await self.rbac.assign_role("admin-1", Role.ADMIN)
        perm = Permission(resource="anything", action="anything")
        assert await self.rbac.check_permission("admin-1", perm) is True

    @pytest.mark.asyncio
    async def test_user_read_permission(self) -> None:
        await self.rbac.assign_role("user-1", Role.USER)
        perm = Permission(resource="agents", action="read")
        assert await self.rbac.check_permission("user-1", perm) is True

    @pytest.mark.asyncio
    async def test_user_write_permission(self) -> None:
        await self.rbac.assign_role("user-1", Role.USER)
        perm = Permission(resource="agents", action="write")
        assert await self.rbac.check_permission("user-1", perm) is True

    @pytest.mark.asyncio
    async def test_user_delete_denied(self) -> None:
        await self.rbac.assign_role("user-1", Role.USER)
        perm = Permission(resource="agents", action="delete")
        assert await self.rbac.check_permission("user-1", perm) is False

    @pytest.mark.asyncio
    async def test_readonly_read_only(self) -> None:
        await self.rbac.assign_role("reader-1", Role.READONLY)
        read_perm = Permission(resource="agents", action="read")
        write_perm = Permission(resource="agents", action="write")
        assert await self.rbac.check_permission("reader-1", read_perm) is True
        assert await self.rbac.check_permission("reader-1", write_perm) is False

    @pytest.mark.asyncio
    async def test_service_read_execute(self) -> None:
        await self.rbac.assign_role("svc-1", Role.SERVICE)
        read_perm = Permission(resource="services", action="read")
        exec_perm = Permission(resource="services", action="execute")
        write_perm = Permission(resource="services", action="write")
        assert await self.rbac.check_permission("svc-1", read_perm) is True
        assert await self.rbac.check_permission("svc-1", exec_perm) is True
        assert await self.rbac.check_permission("svc-1", write_perm) is False

    @pytest.mark.asyncio
    async def test_no_roles_denied(self) -> None:
        perm = Permission(resource="agents", action="read")
        assert await self.rbac.check_permission("noroles-user", perm) is False

    @pytest.mark.asyncio
    async def test_set_user_roles(self) -> None:
        await self.rbac.set_user_roles("user-1", [Role.ADMIN, Role.SERVICE])
        roles = await self.rbac.get_user_roles("user-1")
        assert Role.ADMIN in roles
        assert Role.SERVICE in roles
        assert len(roles) == 2

    @pytest.mark.asyncio
    async def test_permission_denied_event(self) -> None:
        self.rbac.clear_events()
        perm = Permission(resource="agents", action="delete")
        await self.rbac.check_permission("noroles-user", perm)
        assert len(self.rbac.events) > 0
