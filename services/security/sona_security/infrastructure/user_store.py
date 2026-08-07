"""In-memory user store for the Security Layer.

Provides user registration, authentication, and lookup capabilities.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog

from sona_security.domain.models import Role
from sona_security.infrastructure.password_service import PasswordService

logger = structlog.get_logger()


@dataclass
class StoredUser:
    """Internal representation of a stored user."""

    user_id: str
    username: str
    password_hash: str
    roles: list[Role]
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    is_active: bool = True


class UserStore:
    """In-memory user store with password hashing."""

    def __init__(self, password_service: PasswordService | None = None) -> None:
        self._password_service = password_service or PasswordService()
        self._users: dict[str, StoredUser] = {}  # user_id -> StoredUser
        self._username_index: dict[str, str] = {}  # username -> user_id

    async def register_user(
        self,
        user_id: str,
        username: str,
        password: str,
        roles: list[Role] | None = None,
    ) -> StoredUser:
        """Register a new user with hashed password.

        Raises:
            ValueError: If username already exists.
        """
        if username in self._username_index:
            raise ValueError(f"Username '{username}' already exists")
        if user_id in self._users:
            raise ValueError(f"User ID '{user_id}' already exists")

        password_hash = self._password_service.hash_password(password)
        user = StoredUser(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            roles=roles or [Role.USER],
        )
        self._users[user_id] = user
        self._username_index[username] = user_id
        logger.info("user_registered", user_id=user_id, username=username)
        return user

    async def authenticate(self, username: str, password: str) -> StoredUser | None:
        """Authenticate a user by username and password.

        Returns:
            The StoredUser if credentials are valid, None otherwise.
        """
        user_id = self._username_index.get(username)
        if user_id is None:
            return None

        user = self._users.get(user_id)
        if user is None or not user.is_active:
            return None

        if not self._password_service.verify_password(password, user.password_hash):
            return None

        return user

    async def get_user_by_id(self, user_id: str) -> StoredUser | None:
        """Get a user by their ID."""
        return self._users.get(user_id)

    async def get_user_by_username(self, username: str) -> StoredUser | None:
        """Get a user by their username."""
        user_id = self._username_index.get(username)
        if user_id is None:
            return None
        return self._users.get(user_id)

    async def list_users(self) -> list[StoredUser]:
        """List all registered users."""
        return list(self._users.values())

    async def update_roles(self, user_id: str, roles: list[Role]) -> bool:
        """Update a user's roles."""
        user = self._users.get(user_id)
        if user is None:
            return False
        user.roles = roles
        return True

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        user = self._users.get(user_id)
        if user is None:
            return False
        user.is_active = False
        return True
