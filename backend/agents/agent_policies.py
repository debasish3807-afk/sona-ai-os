"""Agent behavior policies and enforcement."""

from __future__ import annotations

from dataclasses import dataclass

from agents.schemas import Agent, AgentType
from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentPolicy:
    """Policy governing agent behavior."""

    max_concurrent_tasks: int = 5
    timeout_seconds: float = 300.0
    retry_limit: int = 3
    isolation_level: str = "process"
    resource_limit_mb: int = 512
    allow_delegation: bool = True
    allow_network: bool = False


class PolicyEngine:
    """Manages and enforces agent policies."""

    def __init__(self) -> None:
        self._policies: dict[AgentType, AgentPolicy] = {}

    def set_policy(self, agent_type: AgentType, policy: AgentPolicy) -> None:
        """Set a policy for an agent type."""
        self._policies[agent_type] = policy
        logger.debug("policy_set", agent_type=agent_type.value)

    def get_policy(self, agent_type: AgentType) -> AgentPolicy:
        """Get the policy for an agent type, or a default."""
        return self._policies.get(agent_type, AgentPolicy())

    def enforce(self, agent: Agent, action: str) -> bool:
        """Enforce policy for an agent action. Returns True if allowed."""
        policy = self.get_policy(agent.agent_type)
        if action == "delegate" and not policy.allow_delegation:
            logger.warning("policy_denied", agent_id=agent.agent_id, action=action)
            return False
        if action == "network" and not policy.allow_network:
            logger.warning("policy_denied", agent_id=agent.agent_id, action=action)
            return False
        return True
