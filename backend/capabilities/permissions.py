"""Permission Validator — validates capability permission requests."""

from __future__ import annotations

from capabilities.registry import CapabilityRegistry
from capabilities.schemas import Capability
from config.logging import get_logger

logger = get_logger(__name__)

ALLOWED_PERMISSIONS: list[str] = [
    "filesystem.read",
    "filesystem.write",
    "network.http",
    "network.ws",
    "process.exec",
    "memory.read",
    "memory.write",
    "admin.manage",
]


class PermissionValidator:
    """Validates capability permissions against allowed grants.

    Ensures capabilities only request known permissions and that
    user grants cover the required permissions for execution.
    """

    def validate(self, capability_schema: Capability, requested_permissions: list[str]) -> bool:
        """Validate that requested permissions are all recognized.

        Args:
            capability_schema: The capability requesting permissions.
            requested_permissions: List of permission strings to validate.

        Returns:
            True if all requested permissions are in the allowed set.
        """
        for perm in requested_permissions:
            if perm not in ALLOWED_PERMISSIONS:
                logger.warning(
                    "invalid_permission",
                    capability_id=capability_schema.capability_id,
                    permission=perm,
                )
                return False
        return True

    def get_required(self, capability_id: str, registry: CapabilityRegistry) -> list[str]:
        """Get required permissions for a capability.

        Args:
            capability_id: The capability ID.
            registry: The capability registry.

        Returns:
            List of required permission strings.
        """
        schema = registry.get(capability_id)
        if schema is None:
            return []
        return list(schema.permissions)

    def check_grant(
        self,
        capability_id: str,
        user_permissions: list[str],
        registry: CapabilityRegistry,
    ) -> bool:
        """Check if user permissions cover the capability's requirements.

        Args:
            capability_id: The capability ID.
            user_permissions: Permissions granted to the user.
            registry: The capability registry.

        Returns:
            True if all required permissions are granted.
        """
        required = self.get_required(capability_id, registry)
        for perm in required:
            if perm not in user_permissions:
                logger.warning(
                    "permission_denied",
                    capability_id=capability_id,
                    missing=perm,
                )
                return False
        return True
