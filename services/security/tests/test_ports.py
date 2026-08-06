"""Unit tests for Security Layer abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest

from application.ports import AISafetyPort, AuthenticationPort, AuthorizationPort
from domain.models import AuthToken, Permission, Role


class TestAuthenticationPort:
    """Tests for the AuthenticationPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify AuthenticationPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AuthenticationPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = AuthenticationPort.__abstractmethods__
        assert "authenticate" in abstract_methods
        assert "validate_token" in abstract_methods
        assert "refresh_token" in abstract_methods
        assert "revoke_token" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteAuth(AuthenticationPort):
            async def authenticate(self, credentials: dict) -> AuthToken:
                return AuthToken(
                    token="test",
                    user_id="user-1",
                    roles=[Role.USER],
                    expires_at="2025-01-01T12:00:00Z",
                    issued_at="2025-01-01T00:00:00Z",
                )

            async def validate_token(self, token: str) -> AuthToken | None:
                return None

            async def refresh_token(self, refresh_token: str) -> AuthToken:
                return AuthToken(
                    token="refreshed",
                    user_id="user-1",
                    roles=[Role.USER],
                    expires_at="2025-01-02T00:00:00Z",
                    issued_at="2025-01-01T12:00:00Z",
                )

            async def revoke_token(self, token: str) -> bool:
                return True

        auth = ConcreteAuth()
        assert isinstance(auth, AuthenticationPort)

    def test_partial_implementation_raises(self) -> None:
        """Verify incomplete implementations cannot be instantiated."""

        class PartialAuth(AuthenticationPort):
            async def authenticate(self, credentials: dict) -> AuthToken:
                return AuthToken(
                    token="t",
                    user_id="u",
                    roles=[],
                    expires_at="",
                    issued_at="",
                )

        with pytest.raises(TypeError):
            PartialAuth()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_authenticate_returns_auth_token(self) -> None:
        """Test that a concrete authenticate() returns an AuthToken."""

        class MockAuth(AuthenticationPort):
            async def authenticate(self, credentials: dict) -> AuthToken:
                return AuthToken(
                    token="jwt-token-123",
                    user_id=credentials["username"],
                    roles=[Role.USER],
                    expires_at="2025-01-01T12:00:00Z",
                    issued_at="2025-01-01T00:00:00Z",
                )

            async def validate_token(self, token: str) -> AuthToken | None:
                return None

            async def refresh_token(self, refresh_token: str) -> AuthToken:
                return AuthToken(
                    token="new",
                    user_id="u",
                    roles=[],
                    expires_at="",
                    issued_at="",
                )

            async def revoke_token(self, token: str) -> bool:
                return True

        auth = MockAuth()
        result = await auth.authenticate({"username": "alice", "password": "secret"})
        assert isinstance(result, AuthToken)
        assert result.user_id == "alice"
        assert result.token == "jwt-token-123"

    @pytest.mark.asyncio
    async def test_validate_token_returns_none_for_invalid(self) -> None:
        """Test that validate_token returns None for invalid tokens."""

        class MockAuth(AuthenticationPort):
            async def authenticate(self, credentials: dict) -> AuthToken:
                return AuthToken(
                    token="t",
                    user_id="u",
                    roles=[],
                    expires_at="",
                    issued_at="",
                )

            async def validate_token(self, token: str) -> AuthToken | None:
                if token == "valid-token":
                    return AuthToken(
                        token="valid-token",
                        user_id="user-1",
                        roles=[Role.USER],
                        expires_at="2025-01-01T12:00:00Z",
                        issued_at="2025-01-01T00:00:00Z",
                    )
                return None

            async def refresh_token(self, refresh_token: str) -> AuthToken:
                return AuthToken(
                    token="new",
                    user_id="u",
                    roles=[],
                    expires_at="",
                    issued_at="",
                )

            async def revoke_token(self, token: str) -> bool:
                return True

        auth = MockAuth()
        assert await auth.validate_token("invalid") is None
        result = await auth.validate_token("valid-token")
        assert result is not None
        assert result.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_revoke_token_returns_bool(self) -> None:
        """Test that revoke_token returns a boolean."""

        class MockAuth(AuthenticationPort):
            async def authenticate(self, credentials: dict) -> AuthToken:
                return AuthToken(
                    token="t",
                    user_id="u",
                    roles=[],
                    expires_at="",
                    issued_at="",
                )

            async def validate_token(self, token: str) -> AuthToken | None:
                return None

            async def refresh_token(self, refresh_token: str) -> AuthToken:
                return AuthToken(
                    token="new",
                    user_id="u",
                    roles=[],
                    expires_at="",
                    issued_at="",
                )

            async def revoke_token(self, token: str) -> bool:
                return token == "existing-token"

        auth = MockAuth()
        assert await auth.revoke_token("existing-token") is True
        assert await auth.revoke_token("nonexistent") is False


class TestAuthorizationPort:
    """Tests for the AuthorizationPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify AuthorizationPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AuthorizationPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = AuthorizationPort.__abstractmethods__
        assert "check_permission" in abstract_methods
        assert "get_user_roles" in abstract_methods
        assert "assign_role" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteAuthz(AuthorizationPort):
            async def check_permission(self, user_id: str, permission: Permission) -> bool:
                return True

            async def get_user_roles(self, user_id: str) -> list[Role]:
                return [Role.USER]

            async def assign_role(self, user_id: str, role: Role) -> bool:
                return True

        authz = ConcreteAuthz()
        assert isinstance(authz, AuthorizationPort)

    @pytest.mark.asyncio
    async def test_check_permission_returns_bool(self) -> None:
        """Test that check_permission returns True/False correctly."""

        class MockAuthz(AuthorizationPort):
            async def check_permission(self, user_id: str, permission: Permission) -> bool:
                return permission.action == "read"

            async def get_user_roles(self, user_id: str) -> list[Role]:
                return [Role.USER]

            async def assign_role(self, user_id: str, role: Role) -> bool:
                return True

        authz = MockAuthz()
        read_perm = Permission(resource="agents", action="read")
        write_perm = Permission(resource="agents", action="write")
        assert await authz.check_permission("user-1", read_perm) is True
        assert await authz.check_permission("user-1", write_perm) is False

    @pytest.mark.asyncio
    async def test_get_user_roles_returns_list(self) -> None:
        """Test that get_user_roles returns a list of Role values."""

        class MockAuthz(AuthorizationPort):
            async def check_permission(self, user_id: str, permission: Permission) -> bool:
                return True

            async def get_user_roles(self, user_id: str) -> list[Role]:
                if user_id == "admin-user":
                    return [Role.ADMIN, Role.USER]
                return [Role.READONLY]

            async def assign_role(self, user_id: str, role: Role) -> bool:
                return True

        authz = MockAuthz()
        roles = await authz.get_user_roles("admin-user")
        assert Role.ADMIN in roles
        assert Role.USER in roles
        assert len(roles) == 2

    @pytest.mark.asyncio
    async def test_assign_role_returns_bool(self) -> None:
        """Test that assign_role returns a boolean."""

        class MockAuthz(AuthorizationPort):
            async def check_permission(self, user_id: str, permission: Permission) -> bool:
                return True

            async def get_user_roles(self, user_id: str) -> list[Role]:
                return []

            async def assign_role(self, user_id: str, role: Role) -> bool:
                return role != Role.ADMIN  # Deny admin assignment

        authz = MockAuthz()
        assert await authz.assign_role("user-1", Role.USER) is True
        assert await authz.assign_role("user-1", Role.ADMIN) is False


class TestAISafetyPort:
    """Tests for the AISafetyPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify AISafetyPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AISafetyPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = AISafetyPort.__abstractmethods__
        assert "check_input" in abstract_methods
        assert "check_output" in abstract_methods
        assert "audit_log" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteSafety(AISafetyPort):
            async def check_input(self, content: str) -> tuple[bool, str | None]:
                return (True, None)

            async def check_output(self, content: str) -> tuple[bool, str | None]:
                return (True, None)

            async def audit_log(self, event: dict) -> None:
                pass

        safety = ConcreteSafety()
        assert isinstance(safety, AISafetyPort)

    @pytest.mark.asyncio
    async def test_check_input_safe_content(self) -> None:
        """Test that check_input returns (True, None) for safe content."""

        class MockSafety(AISafetyPort):
            async def check_input(self, content: str) -> tuple[bool, str | None]:
                if "dangerous" in content.lower():
                    return (False, "Content contains dangerous material")
                return (True, None)

            async def check_output(self, content: str) -> tuple[bool, str | None]:
                return (True, None)

            async def audit_log(self, event: dict) -> None:
                pass

        safety = MockSafety()
        is_safe, reason = await safety.check_input("Hello, how are you?")
        assert is_safe is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_check_input_unsafe_content(self) -> None:
        """Test that check_input returns (False, reason) for unsafe content."""

        class MockSafety(AISafetyPort):
            async def check_input(self, content: str) -> tuple[bool, str | None]:
                if "dangerous" in content.lower():
                    return (False, "Content contains dangerous material")
                return (True, None)

            async def check_output(self, content: str) -> tuple[bool, str | None]:
                return (True, None)

            async def audit_log(self, event: dict) -> None:
                pass

        safety = MockSafety()
        is_safe, reason = await safety.check_input("This is dangerous content")
        assert is_safe is False
        assert reason is not None
        assert "dangerous" in reason.lower()

    @pytest.mark.asyncio
    async def test_check_output_returns_tuple(self) -> None:
        """Test that check_output returns a (bool, str | None) tuple."""

        class MockSafety(AISafetyPort):
            async def check_input(self, content: str) -> tuple[bool, str | None]:
                return (True, None)

            async def check_output(self, content: str) -> tuple[bool, str | None]:
                if len(content) > 10000:
                    return (False, "Output exceeds safe length")
                return (True, None)

            async def audit_log(self, event: dict) -> None:
                pass

        safety = MockSafety()
        is_safe, reason = await safety.check_output("Short safe response")
        assert is_safe is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_audit_log_accepts_event_dict(self) -> None:
        """Test that audit_log accepts an event dictionary."""
        logged_events: list[dict] = []

        class MockSafety(AISafetyPort):
            async def check_input(self, content: str) -> tuple[bool, str | None]:
                return (True, None)

            async def check_output(self, content: str) -> tuple[bool, str | None]:
                return (True, None)

            async def audit_log(self, event: dict) -> None:
                logged_events.append(event)

        safety = MockSafety()
        event = {
            "event_type": "input_check",
            "timestamp": "2025-01-01T00:00:00Z",
            "user_id": "user-123",
            "content_hash": "abc123",
            "outcome": "safe",
        }
        await safety.audit_log(event)
        assert len(logged_events) == 1
        assert logged_events[0]["event_type"] == "input_check"
        assert logged_events[0]["user_id"] == "user-123"
