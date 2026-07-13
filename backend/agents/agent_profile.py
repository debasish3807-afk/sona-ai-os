"""Agent capabilities and metadata profiles."""

from __future__ import annotations

from typing import Any

from agents.schemas import AgentType
from config.logging import get_logger

logger = get_logger(__name__)


class AgentProfile:
    """Defines an agent's capabilities and resource requirements."""

    def __init__(self, agent_type: AgentType) -> None:
        self.agent_type = agent_type
        self.capabilities: list[str] = []
        self.specializations: list[str] = []
        self.max_concurrent: int = 3
        self.timeout_seconds: float = 300.0
        self.retry_limit: int = 3
        self.resource_requirements: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize profile to dictionary."""
        return {
            "agent_type": self.agent_type.value,
            "capabilities": self.capabilities,
            "specializations": self.specializations,
            "max_concurrent": self.max_concurrent,
            "timeout_seconds": self.timeout_seconds,
            "retry_limit": self.retry_limit,
            "resource_requirements": self.resource_requirements,
        }


class ProfileRegistry:
    """Registry of agent profiles by type."""

    def __init__(self) -> None:
        self._profiles: dict[AgentType, AgentProfile] = {}

    def register(self, agent_type: AgentType, profile: AgentProfile) -> None:
        """Register a profile for an agent type."""
        self._profiles[agent_type] = profile
        logger.debug("profile_registered", agent_type=agent_type.value)

    def get(self, agent_type: AgentType) -> AgentProfile | None:
        """Get the profile for an agent type."""
        return self._profiles.get(agent_type)

    def list_all(self) -> dict[str, AgentProfile]:
        """List all registered profiles."""
        return {k.value: v for k, v in self._profiles.items()}
