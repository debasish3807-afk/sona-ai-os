"""Role-Based Access Control engine implementing AuthorizationPort.

Manages role assignments and permission checks based on a configurable
role-to-permission mapping.
"""

import structlog

from sona_security.application.ports import AuthorizationPort
from sona_security.domain.events import PermissionDeniedEvent
from sona_security.domain.models import Permission, Role

logger = structlog.get_logger()

# Default role permissions matrix
DEFAULT_ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.ADMIN: [
        Permission(resource="*", action="*"),
    ],
    Role.USER: [
        Permission(resource="*", action="read", conditions={"owner_only": True}),
        Permission(resource="*", action="write", conditions={"owner_only": True}),
        Permission(resource="*", action="create"),
    ],
    Role.SERVICE: [
        Permission(resource="*", action="read"),
        Permission(resource="*", action="execute"),
    ],
    Role.READONLY: [
        Permission(resource="*", action="read"),
    ],
}


class RBACEngine(AuthorizationPort):
    """Role-Based Access Control engine implementing AuthorizationPort."""

    def __init__(
        self,
        role_permissions: dict[Role, list[Permission]] | None = None,
    ) -> None:
        self._role_permissions = role_permissions or DEFAULT_ROLE_PERMISSIONS
        self._user_roles: dict[str, list[Role]] = {}
        self._events: list[object] = []

    @property
    def events(self) -> list[object]:
        """Access collected domain events."""
        return self._events

    def clear_events(self) -> None:
        """Clear collected domain events."""
        self._events.clear()

    async def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if a user has the specified permission based on their roles."""
        roles = self._user_roles.get(user_id, [])
        if not roles:
            self._events.append(
                PermissionDeniedEvent(
                    user_id=user_id,
                    resource=permission.resource,
                    action=permission.action,
                )
            )
            return False

        for role in roles:
            role_perms = self._role_permissions.get(role, [])
            for role_perm in role_perms:
                if self._permission_matches(role_perm, permission):
                    return True

        self._events.append(
            PermissionDeniedEvent(
                user_id=user_id,
                resource=permission.resource,
                action=permission.action,
            )
        )
        logger.info(
            "permission_denied",
            user_id=user_id,
            resource=permission.resource,
            action=permission.action,
        )
        return False

    async def get_user_roles(self, user_id: str) -> list[Role]:
        """Get all roles assigned to a user."""
        return self._user_roles.get(user_id, [])

    async def assign_role(self, user_id: str, role: Role) -> bool:
        """Assign a role to a user."""
        if user_id not in self._user_roles:
            self._user_roles[user_id] = []
        if role not in self._user_roles[user_id]:
            self._user_roles[user_id].append(role)
            logger.info("role_assigned", user_id=user_id, role=role.value)
        return True

    async def remove_role(self, user_id: str, role: Role) -> bool:
        """Remove a role from a user."""
        if user_id not in self._user_roles:
            return False
        if role in self._user_roles[user_id]:
            self._user_roles[user_id].remove(role)
            logger.info("role_removed", user_id=user_id, role=role.value)
            return True
        return False

    async def set_user_roles(self, user_id: str, roles: list[Role]) -> None:
        """Set all roles for a user (replaces existing)."""
        self._user_roles[user_id] = list(roles)

    def _permission_matches(self, role_perm: Permission, requested: Permission) -> bool:
        """Check if a role permission satisfies a requested permission."""
        # Wildcard resource match
        resource_match = role_perm.resource == "*" or role_perm.resource == requested.resource
        # Wildcard action match
        action_match = role_perm.action == "*" or role_perm.action == requested.action
        return resource_match and action_match
