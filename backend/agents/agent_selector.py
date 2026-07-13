"""Intelligent agent selection for task assignment."""

from __future__ import annotations

from agents.agent_registry import AgentRegistry
from agents.schemas import Agent, AgentState
from config.logging import get_logger

logger = get_logger(__name__)


class AgentSelector:
    """Selects the best agents for given capabilities."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def select_best(self, capability: str, count: int = 1) -> list[Agent]:
        """Select the best agents for a given capability."""
        candidates = self._registry.discover(capability)
        candidates = [a for a in candidates if a.state in (AgentState.IDLE, AgentState.CREATED)]
        ranked = self._rank_agents(candidates, capability)
        return ranked[:count]

    def select_team(self, capabilities: list[str]) -> list[Agent]:
        """Select a team of agents covering all required capabilities."""
        team: list[Agent] = []
        used_ids: set[str] = set()
        for cap in capabilities:
            candidates = self._registry.discover(cap)
            candidates = [a for a in candidates if a.agent_id not in used_ids]
            if candidates:
                ranked = self._rank_agents(candidates, cap)
                best = ranked[0]
                team.append(best)
                used_ids.add(best.agent_id)
        return team

    def _rank_agents(self, agents: list[Agent], capability: str) -> list[Agent]:
        """Rank agents by suitability for a capability."""

        # Prefer idle agents, then by priority
        def sort_key(agent: Agent) -> tuple[int, int]:
            state_score = 0 if agent.state == AgentState.IDLE else 1
            return (state_score, int(agent.priority))

        return sorted(agents, key=sort_key)
