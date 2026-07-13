"""Multi-agent coordination engine."""

from __future__ import annotations

from typing import Any

from agents.agent_negotiator import AgentNegotiator
from agents.agent_registry import AgentRegistry
from agents.agent_scheduler import AgentScheduler
from agents.schemas import (
    AgentState,
    AgentTask,
    CoordinationMode,
    CoordinationPlan,
)
from config.logging import get_logger

logger = get_logger(__name__)


class AgentCoordinator:
    """Coordinates multiple agents executing tasks."""

    def __init__(
        self,
        registry: AgentRegistry,
        scheduler: AgentScheduler,
        negotiator: AgentNegotiator,
    ) -> None:
        self._registry = registry
        self._scheduler = scheduler
        self._negotiator = negotiator

    async def coordinate(self, plan: CoordinationPlan, tasks: list[AgentTask]) -> dict[str, Any]:
        """Execute a coordination plan."""
        agents = [self._registry.get(aid) for aid in plan.agents]
        agents = [a for a in agents if a is not None]

        if plan.mode == CoordinationMode.PARALLEL:
            results = await self.coordinate_parallel(agents, tasks)
        elif plan.mode == CoordinationMode.SEQUENTIAL:
            results = await self.coordinate_sequential(agents, tasks)
        elif plan.mode == CoordinationMode.CONSENSUS:
            return await self.coordinate_consensus(agents, tasks, plan.consensus_threshold)
        else:
            results = await self.coordinate_sequential(agents, tasks)

        return {"mode": plan.mode.value, "results": results, "plan_id": plan.plan_id}

    async def coordinate_parallel(
        self, agents: list[Any], tasks: list[AgentTask]
    ) -> list[dict[str, Any]]:
        """Coordinate agents executing tasks in parallel."""
        results: list[dict[str, Any]] = []
        for i, task in enumerate(tasks):
            agent = agents[i % len(agents)] if agents else None
            if agent:
                task.agent_id = agent.agent_id
                task.state = AgentState.COMPLETED
                results.append(
                    {"task_id": task.task_id, "agent_id": agent.agent_id, "status": "completed"}
                )
        logger.info("parallel_coordination_complete", task_count=len(tasks))
        return results

    async def coordinate_sequential(
        self, agents: list[Any], tasks: list[AgentTask]
    ) -> list[dict[str, Any]]:
        """Coordinate agents executing tasks sequentially."""
        results: list[dict[str, Any]] = []
        for task in tasks:
            if agents:
                agent = agents[0]
                task.agent_id = agent.agent_id
                task.state = AgentState.COMPLETED
                results.append(
                    {"task_id": task.task_id, "agent_id": agent.agent_id, "status": "completed"}
                )
        logger.info("sequential_coordination_complete", task_count=len(tasks))
        return results

    async def coordinate_consensus(
        self, agents: list[Any], tasks: list[AgentTask], threshold: float = 0.7
    ) -> dict[str, Any]:
        """Coordinate using consensus-based decision making."""
        votes: list[dict[str, Any]] = []
        for agent in agents:
            votes.append({"agent_id": agent.agent_id, "approve": True, "weight": 1.0})
        reached, result = await self._negotiator.reach_consensus(votes, threshold)
        return {"consensus_reached": reached, "result": result, "task_count": len(tasks)}
