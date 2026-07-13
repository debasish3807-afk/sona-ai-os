"""Security enforcement for the agent system."""

from __future__ import annotations

from agents.agent_permissions import AgentPermissions, Permission
from agents.agent_policies import PolicyEngine
from agents.schemas import AgentMessage
from config.logging import get_logger

logger = get_logger(__name__)


class AgentSecurity:
    """Enforces security policies and permissions for agents."""

    def __init__(self, permissions: AgentPermissions, policies: PolicyEngine) -> None:
        self._permissions = permissions
        self._policies = policies
        self._audit_log: list[dict[str, object]] = []

    def validate_action(self, agent_id: str, action: str) -> bool:
        """Validate that an agent is allowed to perform an action."""
        perm_map = {
            "read": Permission.READ,
            "write": Permission.WRITE,
            "execute": Permission.EXECUTE,
            "delegate": Permission.DELEGATE,
            "supervise": Permission.SUPERVISE,
            "admin": Permission.ADMIN,
        }
        required = perm_map.get(action)
        if required is None:
            self.audit_action(agent_id, action, False)
            return False
        allowed = self._permissions.has_permission(agent_id, required)
        self.audit_action(agent_id, action, allowed)
        return allowed

    def validate_delegation(self, source_id: str, target_id: str) -> bool:
        """Validate that source can delegate to target."""
        can_delegate = self._permissions.has_permission(source_id, Permission.DELEGATE)
        self.audit_action(source_id, f"delegate_to:{target_id}", can_delegate)
        return can_delegate

    def validate_message(self, message: AgentMessage) -> bool:
        """Validate a message between agents."""
        can_send = self._permissions.has_permission(message.source, Permission.WRITE)
        self.audit_action(message.source, f"message_to:{message.destination}", can_send)
        return can_send

    def audit_action(self, agent_id: str, action: str, allowed: bool) -> None:
        """Record an audit entry."""
        entry = {"agent_id": agent_id, "action": action, "allowed": allowed}
        self._audit_log.append(entry)
        if not allowed:
            logger.warning("security_denied", agent_id=agent_id, action=action)
