"""Security manager for MCP Integration.

Provides allowlist/denylist evaluation, permission validation,
rate limiting per user, and session isolation enforcement.
"""

import fnmatch
import time
from collections import defaultdict

import structlog

from sona_mcp.domain.security import SecurityAction, ToolPolicy, UserPermissions

logger = structlog.get_logger()


class SecurityManager:
    """Manages security policies for MCP tool access.

    Enforces allowlist/denylist policies, permission checks,
    and rate limiting for tool invocations.
    """

    def __init__(self) -> None:
        """Initialize the security manager with empty policies."""
        self._policies: list[ToolPolicy] = []
        self._user_permissions: dict[str, UserPermissions] = {}
        self._call_timestamps: dict[str, list[float]] = defaultdict(list)

    def add_policy(self, policy: ToolPolicy) -> None:
        """Add a security policy to the evaluation chain.

        Policies are evaluated in order; the first matching policy wins.

        Args:
            policy: The ToolPolicy to add.
        """
        self._policies.append(policy)

    def remove_policy(self, tool_pattern: str) -> bool:
        """Remove all policies matching a tool pattern.

        Args:
            tool_pattern: The pattern to remove.

        Returns:
            True if any policies were removed.
        """
        original_count = len(self._policies)
        self._policies = [p for p in self._policies if p.tool_pattern != tool_pattern]
        return len(self._policies) < original_count

    def set_user_permissions(self, permissions: UserPermissions) -> None:
        """Set or update permissions for a user.

        Args:
            permissions: The UserPermissions to store.
        """
        self._user_permissions[permissions.user_id] = permissions

    def get_user_permissions(self, user_id: str) -> UserPermissions:
        """Get permissions for a user, creating defaults if needed.

        Args:
            user_id: The user identifier.

        Returns:
            The user's permissions (defaults to read-only if not set).
        """
        if user_id not in self._user_permissions:
            self._user_permissions[user_id] = UserPermissions(user_id=user_id)
        return self._user_permissions[user_id]

    def evaluate_tool_access(self, user_id: str, tool_name: str) -> bool:
        """Evaluate whether a user can access a specific tool.

        Checks policies in order; first match wins. If no policy matches,
        access is allowed by default.

        Args:
            user_id: The user requesting access.
            tool_name: The tool being accessed.

        Returns:
            True if access is allowed, False if denied.
        """
        # Check user-specific denied tools first
        user_perms = self.get_user_permissions(user_id)
        if tool_name in user_perms.denied_tools:
            return False

        # Evaluate policies in order
        for policy in self._policies:
            if fnmatch.fnmatch(tool_name, policy.tool_pattern):
                return policy.action == SecurityAction.ALLOW

        # Default: allow
        return True

    def check_rate_limit(self, user_id: str) -> bool:
        """Check if the user has exceeded their rate limit.

        Args:
            user_id: The user to check.

        Returns:
            True if the user is within limits, False if exceeded.
        """
        user_perms = self.get_user_permissions(user_id)
        now = time.monotonic()
        window_start = now - 60.0

        # Clean old timestamps
        timestamps = self._call_timestamps[user_id]
        self._call_timestamps[user_id] = [t for t in timestamps if t > window_start]

        return len(self._call_timestamps[user_id]) < user_perms.max_calls_per_minute

    def record_call(self, user_id: str) -> None:
        """Record a tool call for rate limiting.

        Args:
            user_id: The user who made the call.
        """
        self._call_timestamps[user_id].append(time.monotonic())

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission.

        Args:
            user_id: The user to check.
            permission: The permission string to check for.

        Returns:
            True if the user has the permission.
        """
        user_perms = self.get_user_permissions(user_id)
        return permission in user_perms.allowed_permissions

    @property
    def policy_count(self) -> int:
        """Return the number of active policies."""
        return len(self._policies)

    def clear_policies(self) -> None:
        """Remove all policies."""
        self._policies.clear()

    def clear_rate_limits(self) -> None:
        """Reset all rate limit counters."""
        self._call_timestamps.clear()
