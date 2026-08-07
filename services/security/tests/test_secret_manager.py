"""Tests for the secret manager."""

import pytest

from sona_security.infrastructure.secret_manager import SecretConfig, SecretManager


class TestSecretManager:
    def setup_method(self) -> None:
        self.manager = SecretManager()

    @pytest.mark.asyncio
    async def test_load_secrets_from_env(self) -> None:
        env = {
            "SONA_JWT_SECRET": "my-secret",
            "SONA_DB_PASSWORD": "dbpass",
            "OTHER_VAR": "ignored",
        }
        await self.manager.load_secrets(env_override=env)
        assert self.manager.is_loaded is True
        assert self.manager.get_secret("JWT_SECRET") == "my-secret"
        assert self.manager.get_secret("DB_PASSWORD") == "dbpass"

    @pytest.mark.asyncio
    async def test_non_prefixed_vars_ignored(self) -> None:
        env = {"OTHER_VAR": "ignored", "SONA_KEY": "value"}
        await self.manager.load_secrets(env_override=env)
        assert self.manager.get_secret("OTHER_VAR") is None

    @pytest.mark.asyncio
    async def test_validate_required_all_present(self) -> None:
        config = SecretConfig(required_secrets=["JWT_SECRET"])
        manager = SecretManager(config=config)
        await manager.load_secrets(env_override={"SONA_JWT_SECRET": "value"})
        valid, missing = await manager.validate_required()
        assert valid is True
        assert missing == []

    @pytest.mark.asyncio
    async def test_validate_required_missing(self) -> None:
        config = SecretConfig(required_secrets=["JWT_SECRET", "DB_PASSWORD"])
        manager = SecretManager(config=config)
        await manager.load_secrets(env_override={"SONA_JWT_SECRET": "value"})
        valid, missing = await manager.validate_required()
        assert valid is False
        assert "SONA_DB_PASSWORD" in missing

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self) -> None:
        await self.manager.load_secrets(env_override={})
        assert self.manager.get_secret("NONEXISTENT") is None

    @pytest.mark.asyncio
    async def test_set_secret(self) -> None:
        await self.manager.load_secrets(env_override={})
        self.manager.set_secret("NEW_KEY", "new_value")
        assert self.manager.get_secret("NEW_KEY") == "new_value"

    @pytest.mark.asyncio
    async def test_has_secret(self) -> None:
        await self.manager.load_secrets(env_override={"SONA_KEY": "val"})
        assert self.manager.has_secret("KEY") is True
        assert self.manager.has_secret("MISSING") is False

    def test_mask_value_short(self) -> None:
        masked = self.manager.mask_value("ab")
        assert masked == "**"

    def test_mask_value_normal(self) -> None:
        masked = self.manager.mask_value("secretvalue123")
        assert masked.startswith("secr")
        assert "*" in masked
        assert masked != "secretvalue123"

    @pytest.mark.asyncio
    async def test_list_keys(self) -> None:
        await self.manager.load_secrets(env_override={"SONA_A": "1", "SONA_B": "2"})
        keys = self.manager.list_keys()
        assert "SONA_A" in keys
        assert "SONA_B" in keys

    @pytest.mark.asyncio
    async def test_custom_prefix(self) -> None:
        config = SecretConfig(prefix="APP_")
        manager = SecretManager(config=config)
        await manager.load_secrets(env_override={"APP_KEY": "val", "SONA_KEY": "ignored"})
        assert manager.get_secret("KEY") == "val"
        assert manager.get_secret("SONA_KEY") is None

    @pytest.mark.asyncio
    async def test_is_loaded_before_load(self) -> None:
        manager = SecretManager()
        assert manager.is_loaded is False
