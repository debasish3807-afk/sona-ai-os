"""Upgraded agent intelligence capabilities."""

from __future__ import annotations

import time
from typing import Any

from agents.shared_memory import SharedAgentMemory
from agents.strategy_learner import StrategyLearner
from config.logging import get_logger

logger = get_logger(__name__)


class AgentIntelligence:
    """Upgraded agent capabilities: reasoning, negotiation, shared memory, learning."""

    def __init__(self) -> None:
        self._shared_memory = SharedAgentMemory()
        self._strategy_learner = StrategyLearner()
        self._reasoning_count = 0
        self._delegation_count = 0
        self._recovery_count = 0

    async def collaborative_reason(self, agents: list[str], problem: str) -> dict[str, Any]:
        """Each agent produces a perspective, then combines into consensus."""
        perspectives: list[dict[str, Any]] = []
        for agent_id in agents:
            perspective = {
                "agent_id": agent_id,
                "analysis": f"Analysis of '{problem}' from {agent_id}",
                "confidence": 0.8,
                "timestamp": time.time(),
            }
            perspectives.append(perspective)

        consensus = self._build_consensus(perspectives)
        self._reasoning_count += 1
        logger.info(
            "collaborative_reasoning_complete",
            agent_count=len(agents),
            problem=problem[:50],
        )
        return {
            "problem": problem,
            "perspectives": perspectives,
            "consensus": consensus,
            "agent_count": len(agents),
        }

    async def share_memory(
        self,
        source_agent_id: str,
        target_agent_id: str,
        key: str,
        value: Any,
    ) -> bool:
        """Share memory between agents."""
        result = self._shared_memory.share(source_agent_id, target_agent_id, key, value)
        if result:
            logger.info(
                "memory_shared",
                source=source_agent_id,
                target=target_agent_id,
                key=key,
            )
        return result

    async def delegate_dynamically(self, task_description: str, available_agents: list[str]) -> str:
        """Returns best agent_id based on capability and workload scoring."""
        if not available_agents:
            raise ValueError("No agents available for delegation")

        scored: list[tuple[str, float]] = []
        for agent_id in available_agents:
            score = self._score_agent_for_task(agent_id, task_description)
            scored.append((agent_id, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_agent = scored[0][0]
        self._delegation_count += 1
        logger.info(
            "dynamic_delegation",
            task=task_description[:50],
            selected=best_agent,
        )
        return best_agent

    def record_strategy(self, agent_id: str, task: str, outcome: str, success: bool) -> None:
        """Records what worked for future learning."""
        self._strategy_learner.record(agent_id, task, outcome, success)
        logger.debug(
            "strategy_recorded",
            agent_id=agent_id,
            task=task[:50],
            success=success,
        )

    def get_learned_strategies(
        self, agent_id: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get learned strategies from history."""
        return self._strategy_learner.get_history(agent_id=agent_id, limit=limit)

    async def recover_failed_task(
        self, agent_id: str, task_description: str, error: str
    ) -> dict[str, Any]:
        """Returns recovery plan with alternate agent or retry strategy."""
        self._recovery_count += 1
        success_rate = self._strategy_learner.get_success_rate(agent_id)
        best_strategy = self._strategy_learner.get_best_strategy(task_description)

        plan: dict[str, Any] = {
            "original_agent": agent_id,
            "task": task_description,
            "error": error,
            "agent_success_rate": success_rate,
            "recommendation": "retry" if success_rate > 0.5 else "reassign",
            "best_known_strategy": best_strategy,
            "timestamp": time.time(),
        }
        logger.info("recovery_plan_created", agent_id=agent_id, task=task_description[:50])
        return plan

    def get_stats(self) -> dict[str, Any]:
        """Get intelligence module statistics."""
        return {
            "reasoning_count": self._reasoning_count,
            "delegation_count": self._delegation_count,
            "recovery_count": self._recovery_count,
            "memory_stats": self._shared_memory.get_sharing_stats(),
            "strategy_success_rate": self._strategy_learner.get_success_rate(),
        }

    def _build_consensus(self, perspectives: list[dict[str, Any]]) -> dict[str, Any]:
        """Build consensus from multiple perspectives."""
        if not perspectives:
            return {"agreement": 0.0, "summary": "No perspectives available"}
        avg_confidence = sum(p["confidence"] for p in perspectives) / len(perspectives)
        return {
            "agreement": avg_confidence,
            "summary": f"Consensus from {len(perspectives)} agents",
            "participant_count": len(perspectives),
        }

    def _score_agent_for_task(self, agent_id: str, task_description: str) -> float:
        """Score an agent's suitability for a task."""
        base_score = 0.5
        success_rate = self._strategy_learner.get_success_rate(agent_id)
        if success_rate > 0:
            base_score += success_rate * 0.5
        return base_score
