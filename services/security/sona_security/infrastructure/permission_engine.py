"""Permission evaluation engine.

Provides advanced permission evaluation with conditions, ownership checks,
and policy chaining.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_security.domain.models import Permission, Role

logger = structlog.get_logger()


@dataclass
class PolicyContext:
    """Context for policy evaluation."""

    user_id: str
    resource_owner_id: str | None = None
    timestamp: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyResult:
    """Result of a policy evaluation."""

    allowed: bool
    reason: str = ""
    conditions_met: list[str] = field(default_factory=list)
    conditions_failed: list[str] = field(default_factory=list)


class PermissionEngine:
    """Advanced permission evaluation engine with condition support."""

    def __init__(self) -> None:
        self._policies: list[dict[str, Any]] = []

    def add_policy(self, policy: dict[str, Any]) -> None:
        """Add a policy rule to the evaluation chain."""
        self._policies.append(policy)

    async def evaluate(
        self,
        permission: Permission,
        roles: list[Role],
        context: PolicyContext,
    ) -> PolicyResult:
        """Evaluate a permission request against roles and context."""
        conditions_met: list[str] = []
        conditions_failed: list[str] = []

        # Check basic role-based access
        has_role_access = self._check_role_access(permission, roles)
        if not has_role_access:
            return PolicyResult(
                allowed=False,
                reason="no_matching_role_permission",
                conditions_failed=["role_check"],
            )

        conditions_met.append("role_check")

        # Check conditions
        if permission.conditions:
            condition_result = self._evaluate_conditions(permission.conditions, context)
            if not condition_result:
                conditions_failed.append("permission_conditions")
                return PolicyResult(
                    allowed=False,
                    reason="conditions_not_met",
                    conditions_met=conditions_met,
                    conditions_failed=conditions_failed,
                )
            conditions_met.append("permission_conditions")

        # Check custom policies
        for policy in self._policies:
            policy_result = self._evaluate_policy(policy, permission, context)
            if policy_result is False:
                conditions_failed.append(f"policy:{policy.get('name', 'unnamed')}")
                return PolicyResult(
                    allowed=False,
                    reason=f"policy_denied:{policy.get('name', 'unnamed')}",
                    conditions_met=conditions_met,
                    conditions_failed=conditions_failed,
                )
            if policy_result is True:
                conditions_met.append(f"policy:{policy.get('name', 'unnamed')}")

        return PolicyResult(
            allowed=True,
            reason="all_checks_passed",
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
        )

    def _check_role_access(self, permission: Permission, roles: list[Role]) -> bool:
        """Check if any of the user's roles grant the requested permission."""
        for role in roles:
            if role == Role.ADMIN:
                return True
            if role == Role.READONLY and permission.action == "read":
                return True
            if role == Role.SERVICE and permission.action in ("read", "execute"):
                return True
            if role == Role.USER and permission.action in ("read", "write", "create"):
                return True
        return False

    def _evaluate_conditions(self, conditions: dict[str, Any], context: PolicyContext) -> bool:
        """Evaluate permission conditions against context."""
        # Owner-only check
        if conditions.get("owner_only") and context.resource_owner_id:
            if context.user_id != context.resource_owner_id:
                return False

        # Time-based conditions
        if "time_window" in conditions and context.timestamp:
            window = conditions["time_window"]
            start = window.get("start", "00:00")
            end = window.get("end", "23:59")
            # Simple hour-based check
            try:
                current_time = (
                    context.timestamp.split("T")[1][:5] if "T" in context.timestamp else "12:00"
                )
                if not (start <= current_time <= end):
                    return False
            except (IndexError, ValueError):
                pass

        return True

    def _evaluate_policy(
        self, policy: dict[str, Any], permission: Permission, context: PolicyContext
    ) -> bool | None:
        """Evaluate a single policy. Returns True/False/None (no opinion)."""
        # Resource match
        policy_resource = policy.get("resource", "*")
        if policy_resource != "*" and policy_resource != permission.resource:
            return None  # Policy doesn't apply

        # Action match
        policy_action = policy.get("action", "*")
        if policy_action != "*" and policy_action != permission.action:
            return None  # Policy doesn't apply

        # Effect
        effect = policy.get("effect", "allow")
        if effect == "deny":
            return False
        return True
