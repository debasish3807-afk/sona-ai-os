"""RBAC permissions — maps roles to allowed operations."""

from __future__ import annotations

from enum import Enum

from models.user import UserRole


class Permission(str, Enum):
    """Granular permissions for API operations."""

    CHAT = "chat"
    MEMORY = "memory"
    TOOLS = "tools"
    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    GIT = "git"
    GITHUB = "github"
    DOCUMENTS = "documents"
    ADMIN = "admin"


# Role → permissions mapping
role_permissions: dict[UserRole, set[Permission]] = {
    UserRole.ADMIN: {
        Permission.CHAT,
        Permission.MEMORY,
        Permission.TOOLS,
        Permission.FILESYSTEM,
        Permission.TERMINAL,
        Permission.GIT,
        Permission.GITHUB,
        Permission.DOCUMENTS,
        Permission.ADMIN,
    },
    UserRole.DEVELOPER: {
        Permission.CHAT,
        Permission.MEMORY,
        Permission.TOOLS,
        Permission.FILESYSTEM,
        Permission.TERMINAL,
        Permission.GIT,
        Permission.GITHUB,
        Permission.DOCUMENTS,
    },
    UserRole.USER: {
        Permission.CHAT,
        Permission.MEMORY,
        Permission.DOCUMENTS,
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission.

    Args:
        role: The user's role.
        permission: The required permission.

    Returns:
        True if the role grants the permission.
    """
    perms = role_permissions.get(role, set())
    return permission in perms
