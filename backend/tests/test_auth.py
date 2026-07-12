"""Authentication & RBAC tests — 30+ tests for complete coverage."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPasswordHashing:
    """Test Argon2 password hashing."""

    def test_hash_password(self):
        from auth.passwords import hash_password

        hashed = hash_password("my-secret-password")
        assert hashed.startswith("$argon2")
        assert "my-secret-password" not in hashed

    def test_verify_correct_password(self):
        from auth.passwords import hash_password, verify_password

        hashed = hash_password("correct-password")
        assert verify_password("correct-password", hashed) is True

    def test_verify_wrong_password(self):
        from auth.passwords import hash_password, verify_password

        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_different_hashes_same_password(self):
        from auth.passwords import hash_password

        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2  # Argon2 uses random salt


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        from auth.tokens import create_access_token

        token = create_access_token("user-1", "testuser", "user")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_refresh_token(self):
        from auth.tokens import create_refresh_token

        token = create_refresh_token("user-1")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_decode_valid_access_token(self):
        from auth.tokens import create_access_token, decode_token

        token = create_access_token("user-123", "admin", "admin")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self):
        from auth.tokens import create_refresh_token, decode_token

        token = create_refresh_token("user-456")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        from auth.tokens import decode_token

        result = decode_token("invalid.token.here")
        assert result is None

    def test_decode_empty_token(self):
        from auth.tokens import decode_token

        result = decode_token("")
        assert result is None

    def test_token_contains_expiry(self):
        from auth.tokens import create_access_token, decode_token

        token = create_access_token("u1", "user", "user")
        payload = decode_token(token)
        assert payload is not None
        assert "exp" in payload
        assert "iat" in payload


class TestUserModel:
    """Test user data model."""

    def test_user_creation(self):
        from models.user import User, UserRole

        user = User(username="test", email="test@example.com", role=UserRole.DEVELOPER)
        assert user.user_id is not None
        assert user.username == "test"
        assert user.role == UserRole.DEVELOPER
        assert user.is_active is True

    def test_user_public_dict(self):
        from models.user import User

        user = User(username="pub", email="pub@example.com")
        public = user.to_public_dict()
        assert "password_hash" not in public
        assert public["username"] == "pub"
        assert public["email"] == "pub@example.com"

    def test_user_roles_enum(self):
        from models.user import UserRole

        assert UserRole.ADMIN.value == "admin"
        assert UserRole.DEVELOPER.value == "developer"
        assert UserRole.USER.value == "user"


class TestRBAC:
    """Test role-based access control."""

    def test_admin_has_all_permissions(self):
        from auth.permissions import Permission, has_permission
        from models.user import UserRole

        for perm in Permission:
            assert has_permission(UserRole.ADMIN, perm) is True

    def test_user_has_limited_permissions(self):
        from auth.permissions import Permission, has_permission
        from models.user import UserRole

        assert has_permission(UserRole.USER, Permission.CHAT) is True
        assert has_permission(UserRole.USER, Permission.MEMORY) is True
        assert has_permission(UserRole.USER, Permission.TERMINAL) is False
        assert has_permission(UserRole.USER, Permission.ADMIN) is False

    def test_developer_has_dev_permissions(self):
        from auth.permissions import Permission, has_permission
        from models.user import UserRole

        assert has_permission(UserRole.DEVELOPER, Permission.TOOLS) is True
        assert has_permission(UserRole.DEVELOPER, Permission.FILESYSTEM) is True
        assert has_permission(UserRole.DEVELOPER, Permission.GIT) is True
        assert has_permission(UserRole.DEVELOPER, Permission.ADMIN) is False

    def test_permission_enum_values(self):
        from auth.permissions import Permission

        assert Permission.CHAT.value == "chat"
        assert Permission.ADMIN.value == "admin"
        assert len(Permission) == 9


class TestUserStore:
    """Test user store operations."""

    def test_create_user(self):
        from auth.user_store import create_user, reset_store

        reset_store()
        user = create_user("newuser", "new@example.com", "password123")
        assert user is not None
        assert user.username == "newuser"
        assert user.password_hash.startswith("$argon2")
        reset_store()

    def test_create_duplicate_username(self):
        from auth.user_store import create_user, reset_store

        reset_store()
        create_user("dup", "dup1@example.com", "pass1234")
        result = create_user("dup", "dup2@example.com", "pass5678")
        assert result is None
        reset_store()

    def test_create_duplicate_email(self):
        from auth.user_store import create_user, reset_store

        reset_store()
        create_user("user1", "same@example.com", "pass1234")
        result = create_user("user2", "same@example.com", "pass5678")
        assert result is None
        reset_store()

    def test_authenticate_valid(self):
        from auth.user_store import authenticate_user, create_user, reset_store

        reset_store()
        create_user("authuser", "auth@example.com", "secret123")
        user = authenticate_user("authuser", "secret123")
        assert user is not None
        assert user.username == "authuser"
        reset_store()

    def test_authenticate_wrong_password(self):
        from auth.user_store import authenticate_user, create_user, reset_store

        reset_store()
        create_user("authuser2", "auth2@example.com", "correct")
        user = authenticate_user("authuser2", "wrong")
        assert user is None
        reset_store()

    def test_authenticate_nonexistent_user(self):
        from auth.user_store import authenticate_user, reset_store

        reset_store()
        user = authenticate_user("ghost", "password")
        assert user is None
        reset_store()

    def test_change_password(self):
        from auth.user_store import authenticate_user, change_password, create_user, reset_store

        reset_store()
        user = create_user("chpw", "chpw@example.com", "oldpass1")
        assert user is not None
        success = change_password(user.user_id, "oldpass1", "newpass1")
        assert success is True
        # Old password no longer works
        assert authenticate_user("chpw", "oldpass1") is None
        # New password works
        assert authenticate_user("chpw", "newpass1") is not None
        reset_store()

    def test_change_password_wrong_old(self):
        from auth.user_store import change_password, create_user, reset_store

        reset_store()
        user = create_user("chpw2", "chpw2@example.com", "current")
        assert user is not None
        success = change_password(user.user_id, "wrongold", "newpass")
        assert success is False
        reset_store()

    def test_get_user_by_id(self):
        from auth.user_store import create_user, get_user_by_id, reset_store

        reset_store()
        user = create_user("lookup", "lookup@example.com", "pass1234")
        assert user is not None
        found = get_user_by_id(user.user_id)
        assert found is not None
        assert found.username == "lookup"
        reset_store()

    def test_get_user_by_username(self):
        from auth.user_store import create_user, get_user_by_username, reset_store

        reset_store()
        create_user("findme", "findme@example.com", "pass1234")
        found = get_user_by_username("findme")
        assert found is not None
        assert found.email == "findme@example.com"
        reset_store()

    def test_case_insensitive_username(self):
        from auth.user_store import authenticate_user, create_user, reset_store

        reset_store()
        create_user("CaseSensitive", "case@example.com", "mypass12")
        user = authenticate_user("casesensitive", "mypass12")
        assert user is not None
        reset_store()


class TestMiddleware:
    """Test authentication middleware."""

    def test_get_current_user_no_token(self):
        import asyncio

        from fastapi import HTTPException

        from auth.middleware import get_current_user

        raised = False
        try:
            asyncio.run(get_current_user(None))
        except HTTPException as exc:
            raised = True
            assert exc.status_code == 401
        assert raised

    def test_require_permission_factory(self):
        from auth.middleware import require_permission
        from auth.permissions import Permission

        dep = require_permission(Permission.ADMIN)
        assert callable(dep)

    def test_require_role_factory(self):
        from auth.middleware import require_role
        from models.user import UserRole

        dep = require_role(UserRole.DEVELOPER)
        assert callable(dep)
