"""Agent discovery and tracking registry."""

from __future__ import annotations

from agents.schemas import Agent, AgentState, AgentType
from config.logging import get_logger

logger = get_logger(__name__)


class AgentRegistry:
    """Central registry for agent discovery and tracking."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> bool:
        """Register an agent. Returns True if successful."""
        if agent.agent_id in self._agents:
            logger.warning("agent_already_registered", agent_id=agent.agent_id)
            return False
        self._agents[agent.agent_id] = agent
        logger.info("agent_registered", agent_id=agent.agent_id, name=agent.name)
        return True

    def deregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id not in self._agents:
            return False
        del self._agents[agent_id]
        logger.info("agent_deregistered", agent_id=agent_id)
        return True

    def get(self, agent_id: str) -> Agent | None:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def list_all(self) -> list[Agent]:
        """List all registered agents."""
        return list(self._agents.values())

    def list_by_type(self, agent_type: AgentType) -> list[Agent]:
        """List agents of a specific type."""
        return [a for a in self._agents.values() if a.agent_type == agent_type]

    def list_by_state(self, state: AgentState) -> list[Agent]:
        """List agents in a specific state."""
        return [a for a in self._agents.values() if a.state == state]

    def discover(self, capability: str) -> list[Agent]:
        """Find agents with a specific capability."""
        return [a for a in self._agents.values() if capability in a.capabilities]

    @property
    def count(self) -> int:
        """Total number of registered agents."""
        return len(self._agents)

    def get_stats(self) -> dict[str, int]:
        """Get registry statistics."""
        stats: dict[str, int] = {"total": self.count}
        for state in AgentState:
            agents = self.list_by_state(state)
            if agents:
                stats[state.value] = len(agents)
        return stats
