"""RBAC permissions for agents."""

from __future__ import annotations

from enum import Enum

from config.logging import get_logger

logger = get_logger(__name__)


class Permission(str, Enum):
    """Agent permission levels."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELEGATE = "delegate"
    SUPERVISE = "supervise"
    ADMIN = "admin"


class AgentPermissions:
    """Manages RBAC permissions for agents."""

    def __init__(self) -> None:
        self._grants: dict[str, set[Permission]] = {}

    def grant(self, agent_id: str, permission: Permission) -> None:
        """Grant a permission to an agent."""
        self._grants.setdefault(agent_id, set()).add(permission)
        logger.debug("permission_granted", agent_id=agent_id, permission=permission.value)

    def revoke(self, agent_id: str, permission: Permission) -> None:
        """Revoke a permission from an agent."""
        perms = self._grants.get(agent_id)
        if perms:
            perms.discard(permission)

    def has_permission(self, agent_id: str, permission: Permission) -> bool:
        """Check if an agent has a permission."""
        perms = self._grants.get(agent_id, set())
        return permission in perms

    def get_permissions(self, agent_id: str) -> set[Permission]:
        """Get all permissions for an agent."""
        return self._grants.get(agent_id, set()).copy()
