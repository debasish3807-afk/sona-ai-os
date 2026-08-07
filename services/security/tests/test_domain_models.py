"""Unit tests for Security Layer domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_security.domain.models import AuthToken, Permission, Role


class TestRole:
    """Tests for the Role enum."""

    def test_all_roles_defined(self) -> None:
        """Verify all expected roles are available."""
        assert Role.ADMIN == "admin"
        assert Role.USER == "user"
        assert Role.SERVICE == "service"
        assert Role.READONLY == "readonly"

    def test_role_count(self) -> None:
        """Verify exactly 4 roles exist."""
        assert len(Role) == 4

    def test_role_is_str_enum(self) -> None:
        """Verify roles are usable as strings."""
        assert str(Role.ADMIN) == "admin"
        assert str(Role.USER) == "user"
        assert str(Role.SERVICE) == "service"
        assert str(Role.READONLY) == "readonly"

    def test_role_membership(self) -> None:
        """Verify role membership checks work."""
        assert "admin" in [r.value for r in Role]
        assert "unknown" not in [r.value for r in Role]


class TestAuthToken:
    """Tests for the AuthToken frozen dataclass."""

    def test_creation(self) -> None:
        """Create an AuthToken with all fields."""
        token = AuthToken(
            token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
            user_id="user-123",
            roles=[Role.ADMIN, Role.USER],
            expires_at="2025-01-01T12:00:00Z",
            issued_at="2025-01-01T00:00:00Z",
        )
        assert token.token == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        assert token.user_id == "user-123"
        assert token.roles == [Role.ADMIN, Role.USER]
        assert token.expires_at == "2025-01-01T12:00:00Z"
        assert token.issued_at == "2025-01-01T00:00:00Z"

    def test_single_role(self) -> None:
        """Create an AuthToken with a single role."""
        token = AuthToken(
            token="token-abc",
            user_id="service-456",
            roles=[Role.SERVICE],
            expires_at="2025-06-01T00:00:00Z",
            issued_at="2025-05-01T00:00:00Z",
        )
        assert len(token.roles) == 1
        assert token.roles[0] == Role.SERVICE

    def test_empty_roles(self) -> None:
        """Create an AuthToken with no roles."""
        token = AuthToken(
            token="token-xyz",
            user_id="user-789",
            roles=[],
            expires_at="2025-01-01T12:00:00Z",
            issued_at="2025-01-01T00:00:00Z",
        )
        assert token.roles == []

    def test_is_frozen(self) -> None:
        """Verify AuthToken is immutable."""
        token = AuthToken(
            token="token-frozen",
            user_id="user-001",
            roles=[Role.USER],
            expires_at="2025-01-01T12:00:00Z",
            issued_at="2025-01-01T00:00:00Z",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            token.token = "modified"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Verify AuthToken equality based on field values."""
        token1 = AuthToken(
            token="same-token",
            user_id="user-001",
            roles=[Role.USER],
            expires_at="2025-01-01T12:00:00Z",
            issued_at="2025-01-01T00:00:00Z",
        )
        token2 = AuthToken(
            token="same-token",
            user_id="user-001",
            roles=[Role.USER],
            expires_at="2025-01-01T12:00:00Z",
            issued_at="2025-01-01T00:00:00Z",
        )
        assert token1 == token2


class TestPermission:
    """Tests for the Permission frozen dataclass."""

    def test_creation_with_all_fields(self) -> None:
        """Create a Permission with all fields including conditions."""
        perm = Permission(
            resource="agents",
            action="write",
            conditions={"owner_only": True},
        )
        assert perm.resource == "agents"
        assert perm.action == "write"
        assert perm.conditions == {"owner_only": True}

    def test_creation_without_conditions(self) -> None:
        """Create a Permission with default None conditions."""
        perm = Permission(
            resource="memory",
            action="read",
        )
        assert perm.resource == "memory"
        assert perm.action == "read"
        assert perm.conditions is None

    def test_explicit_none_conditions(self) -> None:
        """Create a Permission with explicit None conditions."""
        perm = Permission(
            resource="workflows",
            action="delete",
            conditions=None,
        )
        assert perm.conditions is None

    def test_is_frozen(self) -> None:
        """Verify Permission is immutable."""
        perm = Permission(
            resource="agents",
            action="read",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            perm.resource = "modified"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Verify Permission equality based on field values."""
        perm1 = Permission(resource="agents", action="read")
        perm2 = Permission(resource="agents", action="read")
        assert perm1 == perm2

    def test_inequality_different_action(self) -> None:
        """Verify Permissions with different actions are not equal."""
        perm1 = Permission(resource="agents", action="read")
        perm2 = Permission(resource="agents", action="write")
        assert perm1 != perm2

    def test_complex_conditions(self) -> None:
        """Create a Permission with complex nested conditions."""
        perm = Permission(
            resource="workflows",
            action="execute",
            conditions={
                "time_window": {"start": "09:00", "end": "17:00"},
                "max_concurrent": 5,
                "allowed_regions": ["us-east-1", "eu-west-1"],
            },
        )
        assert perm.conditions is not None
        assert perm.conditions["max_concurrent"] == 5
        assert len(perm.conditions["allowed_regions"]) == 2
