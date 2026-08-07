"""Tests for the user store."""

import pytest

from sona_security.domain.models import Role
from sona_security.infrastructure.password_service import PasswordService
from sona_security.infrastructure.user_store import UserStore


class TestUserStore:
    def setup_method(self) -> None:
        self.password_svc = PasswordService(iterations=1000)
        self.store = UserStore(password_service=self.password_svc)

    @pytest.mark.asyncio
    async def test_register_user(self) -> None:
        user = await self.store.register_user("u1", "alice", "pass123")
        assert user.user_id == "u1"
        assert user.username == "alice"
        assert user.roles == [Role.USER]
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_register_with_roles(self) -> None:
        user = await self.store.register_user("u2", "bob", "pass", roles=[Role.ADMIN, Role.USER])
        assert user.roles == [Role.ADMIN, Role.USER]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        with pytest.raises(ValueError, match="already exists"):
            await self.store.register_user("u2", "alice", "pass456")

    @pytest.mark.asyncio
    async def test_register_duplicate_user_id(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        with pytest.raises(ValueError, match="already exists"):
            await self.store.register_user("u1", "bob", "pass456")

    @pytest.mark.asyncio
    async def test_authenticate_success(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        user = await self.store.authenticate("alice", "pass123")
        assert user is not None
        assert user.user_id == "u1"

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        user = await self.store.authenticate("alice", "wrong")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_unknown_user(self) -> None:
        user = await self.store.authenticate("unknown", "pass")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        await self.store.deactivate_user("u1")
        user = await self.store.authenticate("alice", "pass123")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        user = await self.store.get_user_by_id("u1")
        assert user is not None
        assert user.username == "alice"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self) -> None:
        user = await self.store.get_user_by_id("nonexistent")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_username(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        user = await self.store.get_user_by_username("alice")
        assert user is not None
        assert user.user_id == "u1"

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self) -> None:
        user = await self.store.get_user_by_username("nonexistent")
        assert user is None

    @pytest.mark.asyncio
    async def test_list_users(self) -> None:
        await self.store.register_user("u1", "alice", "pass1")
        await self.store.register_user("u2", "bob", "pass2")
        users = await self.store.list_users()
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_list_users_empty(self) -> None:
        users = await self.store.list_users()
        assert users == []

    @pytest.mark.asyncio
    async def test_update_roles(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        result = await self.store.update_roles("u1", [Role.ADMIN])
        assert result is True
        user = await self.store.get_user_by_id("u1")
        assert user is not None
        assert user.roles == [Role.ADMIN]

    @pytest.mark.asyncio
    async def test_update_roles_unknown_user(self) -> None:
        result = await self.store.update_roles("unknown", [Role.ADMIN])
        assert result is False

    @pytest.mark.asyncio
    async def test_deactivate_user(self) -> None:
        await self.store.register_user("u1", "alice", "pass123")
        result = await self.store.deactivate_user("u1")
        assert result is True
        user = await self.store.get_user_by_id("u1")
        assert user is not None
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_deactivate_unknown_user(self) -> None:
        result = await self.store.deactivate_user("unknown")
        assert result is False
