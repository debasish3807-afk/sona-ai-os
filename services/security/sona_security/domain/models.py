"""Domain models for the Security Layer service.

Defines the data structures used by the Security Layer for authentication,
authorization, and AI safety operations.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    """Available user/service roles.

    Determines the level of access and permissions granted to an entity
    within the Sona AI OS ecosystem.
    """

    ADMIN = "admin"
    USER = "user"
    SERVICE = "service"
    READONLY = "readonly"


@dataclass(frozen=True)
class AuthToken:
    """An authentication token representing a validated session.

    Attributes:
        token: The opaque token string.
        user_id: The unique identifier of the authenticated user or service.
        roles: List of roles assigned to the token holder.
        expires_at: ISO 8601 timestamp when the token expires.
        issued_at: ISO 8601 timestamp when the token was issued.
    """

    token: str
    user_id: str
    roles: list[Role]
    expires_at: str
    issued_at: str


@dataclass(frozen=True)
class Permission:
    """A permission defining access to a specific resource and action.

    Attributes:
        resource: The resource identifier (e.g., "agents", "memory", "workflows").
        action: The action to perform on the resource (e.g., "read", "write", "delete").
        conditions: Optional conditions that further restrict the permission.
    """

    resource: str
    action: str
    conditions: dict[str, Any] | None = None
