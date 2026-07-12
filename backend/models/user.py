"""User model — core identity data structure."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"


@dataclass
class User:
    """Application user with authentication data."""

    user_id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_login: str | None = None

    def to_public_dict(self) -> dict[str, str | bool | None]:
        """Serialize without password hash."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_login": self.last_login,
        }
