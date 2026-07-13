"""Inter-agent negotiation for task assignment and consensus."""

from __future__ import annotations

from typing import Any

from agents.schemas import Agent, AgentTask
from config.logging import get_logger

logger = get_logger(__name__)


class AgentNegotiator:
    """Handles inter-agent negotiation and consensus."""

    def __init__(self) -> None:
        self._negotiation_history: list[dict[str, Any]] = []

    async def negotiate(self, agents: list[Agent], task: AgentTask) -> Agent:
        """Negotiate which agent should handle a task."""
        if not agents:
            raise ValueError("No agents available for negotiation")
        # Score agents by capability match
        scored = []
        for agent in agents:
            score = sum(1 for c in agent.capabilities if c in task.description)
            scored.append((agent, score))
        scored.sort(key=lambda x: (x[1], -int(x[0].priority)), reverse=True)
        winner = scored[0][0]
        self._negotiation_history.append({"task_id": task.task_id, "winner": winner.agent_id})
        logger.info("negotiation_complete", winner=winner.agent_id)
        return winner

    async def vote(self, agents: list[Agent], proposal: dict[str, Any]) -> dict[str, Any]:
        """Collect votes from agents on a proposal."""
        votes: list[dict[str, Any]] = []
        for agent in agents:
            # Simulated vote: agents vote based on priority alignment
            vote = {"agent_id": agent.agent_id, "approve": True, "weight": 1.0}
            votes.append(vote)
        agreement = self._calculate_agreement(votes)
        return {"votes": votes, "agreement": agreement, "proposal": proposal}

    async def reach_consensus(
        self, votes: list[dict[str, Any]], threshold: float = 0.7
    ) -> tuple[bool, dict[str, Any]]:
        """Determine if consensus is reached from votes."""
        agreement = self._calculate_agreement(votes)
        reached = agreement >= threshold
        result = {"agreement": agreement, "threshold": threshold, "reached": reached}
        if reached:
            logger.info("consensus_reached", agreement=agreement)
        return reached, result

    def _calculate_agreement(self, votes: list[dict[str, Any]]) -> float:
        """Calculate agreement ratio from votes."""
        if not votes:
            return 0.0
        approvals = sum(1 for v in votes if v.get("approve"))
        return approvals / len(votes)
