"""Route tasks to appropriate agents based on capabilities."""

from __future__ import annotations

from agents.agent_registry import AgentRegistry
from agents.schemas import Agent, AgentState
from config.logging import get_logger

logger = get_logger(__name__)


class AgentRouter:
    """Routes tasks to agents based on capability matching."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def route(
        self, task_description: str, required_capabilities: list[str] | None = None
    ) -> list[Agent]:
        """Find agents that can handle a task."""
        candidates = self._registry.list_all()
        # Filter to idle or assigned agents
        candidates = [
            a
            for a in candidates
            if a.state in (AgentState.IDLE, AgentState.ASSIGNED, AgentState.CREATED)
        ]
        if required_capabilities:
            scored = [(a, self._score_agent(a, required_capabilities)) for a in candidates]
            scored.sort(key=lambda x: x[1], reverse=True)
            return [a for a, s in scored if s > 0]
        return candidates

    def route_single(self, task_description: str) -> Agent | None:
        """Route to the single best agent."""
        results = self.route(task_description)
        return results[0] if results else None

    def _score_agent(self, agent: Agent, capabilities: list[str]) -> float:
        """Score an agent based on capability overlap."""
        if not capabilities:
            return 0.0
        matches = sum(1 for c in capabilities if c in agent.capabilities)
        return matches / len(capabilities)
