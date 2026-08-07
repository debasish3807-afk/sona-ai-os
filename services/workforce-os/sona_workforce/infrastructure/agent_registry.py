"""Agent Registry - manages agent registration and lookup."""

from __future__ import annotations

import structlog

from sona_workforce.domain.agent import AgentCapability, AgentProfile, AgentRole, AgentState

logger = structlog.get_logger()


class AgentRegistry:
    """Registry for managing agent profiles.

    Provides registration, unregistration, lookup by type/capability/role,
    and state tracking for all agents in the workforce.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentProfile] = {}

    async def register(self, profile: AgentProfile) -> None:
        """Register an agent profile."""
        self._agents[profile.agent_id] = profile
        await logger.ainfo(
            "agent_registered",
            agent_id=profile.agent_id,
            agent_type=profile.agent_type,
            role=profile.role,
        )

    async def unregister(self, agent_id: str) -> bool:
        """Unregister an agent by ID. Returns True if removed."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            await logger.ainfo("agent_unregistered", agent_id=agent_id)
            return True
        return False

    def get(self, agent_id: str) -> AgentProfile | None:
        """Get an agent profile by ID."""
        return self._agents.get(agent_id)

    def get_by_type(self, agent_type: str) -> list[AgentProfile]:
        """Get all agents of a given type."""
        return [a for a in self._agents.values() if a.agent_type == agent_type]

    def get_by_capability(self, capability: AgentCapability) -> list[AgentProfile]:
        """Get all agents with a given capability."""
        return [a for a in self._agents.values() if capability in a.capabilities]

    def get_by_role(self, role: AgentRole) -> list[AgentProfile]:
        """Get all agents with a given role."""
        return [a for a in self._agents.values() if a.role == role]

    def get_available(self) -> list[AgentProfile]:
        """Get all agents in IDLE state that can accept tasks."""
        return [
            a
            for a in self._agents.values()
            if a.state == AgentState.IDLE and a.active_tasks < a.max_concurrent_tasks
        ]

    def update_state(self, agent_id: str, state: AgentState) -> bool:
        """Update an agent's state. Returns True if successful."""
        profile = self._agents.get(agent_id)
        if profile is not None:
            profile.state = state
            return True
        return False

    def all_agents(self) -> list[AgentProfile]:
        """Return all registered agent profiles."""
        return list(self._agents.values())

    @property
    def count(self) -> int:
        """Return total number of registered agents."""
        return len(self._agents)
