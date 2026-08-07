"""Plugin permission manager — grant, revoke, and check permissions at runtime."""

from __future__ import annotations

import structlog

from sona_plugins.domain.permissions import PluginPermission, PluginPermissionSet

logger = structlog.get_logger()


class PermissionDeniedError(Exception):
    """Raised when a plugin attempts an action without required permission."""

    def __init__(self, plugin_id: str, permission: PluginPermission) -> None:
        self.plugin_id = plugin_id
        self.permission = permission
        super().__init__(f"Permission denied for plugin '{plugin_id}': missing '{permission}'")


class PluginPermissionManager:
    """Manages runtime permission grants and checks for plugins.

    Tracks which permissions each plugin has been granted and
    provides enforcement methods for the sandbox.
    """

    def __init__(self) -> None:
        self._grants: dict[str, set[PluginPermission]] = {}
        self._required: dict[str, set[PluginPermission]] = {}

    def register(self, plugin_id: str, required: frozenset[PluginPermission]) -> None:
        """Register the required permissions for a plugin."""
        self._required[plugin_id] = set(required)
        if plugin_id not in self._grants:
            self._grants[plugin_id] = set()
        logger.info(
            "permissions_registered",
            plugin_id=plugin_id,
            required=sorted(str(p) for p in required),
        )

    def grant(self, plugin_id: str, permission: PluginPermission) -> None:
        """Grant a permission to a plugin."""
        if plugin_id not in self._grants:
            self._grants[plugin_id] = set()
        self._grants[plugin_id].add(permission)
        logger.info("permission_granted", plugin_id=plugin_id, permission=permission)

    def grant_all(self, plugin_id: str, permissions: frozenset[PluginPermission]) -> None:
        """Grant multiple permissions to a plugin."""
        if plugin_id not in self._grants:
            self._grants[plugin_id] = set()
        self._grants[plugin_id].update(permissions)
        logger.info(
            "permissions_granted",
            plugin_id=plugin_id,
            permissions=sorted(str(p) for p in permissions),
        )

    def revoke(self, plugin_id: str, permission: PluginPermission) -> None:
        """Revoke a permission from a plugin."""
        if plugin_id in self._grants:
            self._grants[plugin_id].discard(permission)
            logger.info("permission_revoked", plugin_id=plugin_id, permission=permission)

    def revoke_all(self, plugin_id: str) -> None:
        """Revoke all permissions from a plugin."""
        self._grants.pop(plugin_id, None)
        logger.info("all_permissions_revoked", plugin_id=plugin_id)

    def has_permission(self, plugin_id: str, permission: PluginPermission) -> bool:
        """Check if a plugin has a specific permission."""
        return permission in self._grants.get(plugin_id, set())

    def check_permission(self, plugin_id: str, permission: PluginPermission) -> None:
        """Check permission and raise PermissionDeniedError if not granted."""
        if not self.has_permission(plugin_id, permission):
            raise PermissionDeniedError(plugin_id, permission)

    def get_permission_set(self, plugin_id: str) -> PluginPermissionSet:
        """Get the full permission set (required + granted) for a plugin."""
        required = frozenset(self._required.get(plugin_id, set()))
        granted = frozenset(self._grants.get(plugin_id, set()))
        return PluginPermissionSet(required=required, granted=granted)

    def is_satisfied(self, plugin_id: str) -> bool:
        """Check if all required permissions are satisfied."""
        perm_set = self.get_permission_set(plugin_id)
        return perm_set.is_satisfied()

    def missing_permissions(self, plugin_id: str) -> frozenset[PluginPermission]:
        """Get the set of missing permissions for a plugin."""
        perm_set = self.get_permission_set(plugin_id)
        return perm_set.missing()

    def unregister(self, plugin_id: str) -> None:
        """Remove all permission data for a plugin."""
        self._grants.pop(plugin_id, None)
        self._required.pop(plugin_id, None)

    def get_granted(self, plugin_id: str) -> frozenset[PluginPermission]:
        """Get the set of granted permissions for a plugin."""
        return frozenset(self._grants.get(plugin_id, set()))
