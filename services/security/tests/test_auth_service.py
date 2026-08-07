"""Tests for the authentication service."""

import pytest

from sona_security.application.ports import AuthenticationPort
from sona_security.domain.models import AuthToken, Role
from sona_security.infrastructure.auth_service import AuthService
from sona_security.infrastructure.jwt_service import JWTConfig, JWTService
from sona_security.infrastructure.password_service import PasswordService
from sona_security.infrastructure.user_store import UserStore


class TestAuthService:
    @pytest.fixture
    async def auth_setup(self) -> tuple[AuthService, UserStore, JWTService]:
        jwt_svc = JWTService(config=JWTConfig(secret="test-secret"))
        pwd_svc = PasswordService(iterations=1000)
        user_store = UserStore(password_service=pwd_svc)
        auth_svc = AuthService(jwt_service=jwt_svc, user_store=user_store)
        await user_store.register_user("u1", "alice", "password123", roles=[Role.USER])
        await user_store.register_user("u2", "admin", "adminpass", roles=[Role.ADMIN])
        return auth_svc, user_store, jwt_svc

    @pytest.mark.asyncio
    async def test_implements_authentication_port(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        assert isinstance(auth_svc, AuthenticationPort)

    @pytest.mark.asyncio
    async def test_authenticate_success(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        token = await auth_svc.authenticate({"username": "alice", "password": "password123"})
        assert isinstance(token, AuthToken)
        assert token.user_id == "u1"
        assert Role.USER in token.roles

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        with pytest.raises(ValueError, match="Invalid credentials"):
            await auth_svc.authenticate({"username": "alice", "password": "wrong"})

    @pytest.mark.asyncio
    async def test_authenticate_missing_credentials(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        with pytest.raises(ValueError, match="required"):
            await auth_svc.authenticate({"username": "", "password": ""})

    @pytest.mark.asyncio
    async def test_authenticate_unknown_user(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        with pytest.raises(ValueError, match="Invalid credentials"):
            await auth_svc.authenticate({"username": "nobody", "password": "pass"})

    @pytest.mark.asyncio
    async def test_validate_token(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        token = await auth_svc.authenticate({"username": "alice", "password": "password123"})
        validated = await auth_svc.validate_token(token.token)
        assert validated is not None
        assert validated.user_id == "u1"

    @pytest.mark.asyncio
    async def test_validate_invalid_token(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        result = await auth_svc.validate_token("invalid-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_token(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        token = await auth_svc.authenticate({"username": "alice", "password": "password123"})
        result = await auth_svc.revoke_token(token.token)
        assert result is True
        validated = await auth_svc.validate_token(token.token)
        assert validated is None

    @pytest.mark.asyncio
    async def test_refresh_token(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        _, _, jwt_svc = auth_setup
        auth_svc, _, _ = auth_setup
        refresh = jwt_svc.generate_refresh_token("u1", ["user"])
        new_token = await auth_svc.refresh_token(refresh)
        assert isinstance(new_token, AuthToken)
        assert new_token.user_id == "u1"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        with pytest.raises(ValueError, match="Invalid"):
            await auth_svc.refresh_token("invalid-refresh-token")

    @pytest.mark.asyncio
    async def test_refresh_access_token_fails(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, jwt_svc = auth_setup
        access = jwt_svc.generate_access_token("u1", ["user"])
        with pytest.raises(ValueError, match="not a refresh token"):
            await auth_svc.refresh_token(access)

    @pytest.mark.asyncio
    async def test_login(self, auth_setup: tuple[AuthService, UserStore, JWTService]) -> None:
        auth_svc, _, _ = auth_setup
        result = await auth_svc.login("alice", "password123")
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user_id"] == "u1"

    @pytest.mark.asyncio
    async def test_login_invalid(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        with pytest.raises(ValueError):
            await auth_svc.login("alice", "wrong")

    @pytest.mark.asyncio
    async def test_logout(self, auth_setup: tuple[AuthService, UserStore, JWTService]) -> None:
        auth_svc, _, _ = auth_setup
        result = await auth_svc.login("alice", "password123")
        success = await auth_svc.logout(result["access_token"], result["refresh_token"])
        assert success is True
        validated = await auth_svc.validate_token(result["access_token"])
        assert validated is None

    @pytest.mark.asyncio
    async def test_events_on_success(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        auth_svc.clear_events()
        await auth_svc.authenticate({"username": "alice", "password": "password123"})
        assert len(auth_svc.events) > 0

    @pytest.mark.asyncio
    async def test_events_on_failure(
        self, auth_setup: tuple[AuthService, UserStore, JWTService]
    ) -> None:
        auth_svc, _, _ = auth_setup
        auth_svc.clear_events()
        with pytest.raises(ValueError):
            await auth_svc.authenticate({"username": "alice", "password": "wrong"})
        assert len(auth_svc.events) > 0
