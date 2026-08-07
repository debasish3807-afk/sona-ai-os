"""Tests for the API key service."""

import pytest

from sona_security.infrastructure.api_key_service import APIKeyService


class TestAPIKeyService:
    def setup_method(self) -> None:
        self.svc = APIKeyService()

    @pytest.mark.asyncio
    async def test_generate_key(self) -> None:
        key, metadata = await self.svc.generate_key("user-1", name="test-key")
        assert len(key) == 64  # 32 bytes hex
        assert metadata.user_id == "user-1"
        assert metadata.name == "test-key"
        assert metadata.is_active is True

    @pytest.mark.asyncio
    async def test_generate_key_with_scopes(self) -> None:
        key, metadata = await self.svc.generate_key(
            "user-1", name="admin-key", scopes=["read", "write", "admin"]
        )
        assert metadata.scopes == ["read", "write", "admin"]

    @pytest.mark.asyncio
    async def test_generate_key_default_scopes(self) -> None:
        _, metadata = await self.svc.generate_key("user-1")
        assert metadata.scopes == ["read"]

    @pytest.mark.asyncio
    async def test_validate_valid_key(self) -> None:
        key, _ = await self.svc.generate_key("user-1")
        metadata = await self.svc.validate_key(key)
        assert metadata is not None
        assert metadata.user_id == "user-1"
        assert metadata.last_used is not None

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self) -> None:
        metadata = await self.svc.validate_key("nonexistent-key")
        assert metadata is None

    @pytest.mark.asyncio
    async def test_validate_revoked_key(self) -> None:
        key, _ = await self.svc.generate_key("user-1")
        await self.svc.revoke_key(key)
        metadata = await self.svc.validate_key(key)
        assert metadata is None

    @pytest.mark.asyncio
    async def test_revoke_key(self) -> None:
        key, _ = await self.svc.generate_key("user-1")
        result = await self.svc.revoke_key(key)
        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key(self) -> None:
        result = await self.svc.revoke_key("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_key_by_id(self) -> None:
        _, metadata = await self.svc.generate_key("user-1")
        result = await self.svc.revoke_key_by_id(metadata.key_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_key_by_id_nonexistent(self) -> None:
        result = await self.svc.revoke_key_by_id("no-such-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_keys(self) -> None:
        await self.svc.generate_key("user-1", name="key1")
        await self.svc.generate_key("user-1", name="key2")
        await self.svc.generate_key("user-2", name="key3")
        keys = await self.svc.get_user_keys("user-1")
        assert len(keys) == 2

    @pytest.mark.asyncio
    async def test_get_user_keys_empty(self) -> None:
        keys = await self.svc.get_user_keys("no-keys-user")
        assert keys == []

    @pytest.mark.asyncio
    async def test_check_scope_allowed(self) -> None:
        key, _ = await self.svc.generate_key("user-1", scopes=["read", "write"])
        assert await self.svc.check_scope(key, "read") is True
        assert await self.svc.check_scope(key, "write") is True

    @pytest.mark.asyncio
    async def test_check_scope_denied(self) -> None:
        key, _ = await self.svc.generate_key("user-1", scopes=["read"])
        assert await self.svc.check_scope(key, "admin") is False

    @pytest.mark.asyncio
    async def test_check_scope_wildcard(self) -> None:
        key, _ = await self.svc.generate_key("user-1", scopes=["*"])
        assert await self.svc.check_scope(key, "anything") is True

    @pytest.mark.asyncio
    async def test_check_scope_invalid_key(self) -> None:
        assert await self.svc.check_scope("bad-key", "read") is False

    @pytest.mark.asyncio
    async def test_key_has_prefix(self) -> None:
        key, metadata = await self.svc.generate_key("user-1")
        assert metadata.prefix == key[:8]

    @pytest.mark.asyncio
    async def test_unique_keys(self) -> None:
        keys = set()
        for _ in range(10):
            key, _ = await self.svc.generate_key("user-1")
            keys.add(key)
        assert len(keys) == 10
