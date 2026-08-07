"""Delegation Engine - hierarchical task delegation between agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_workforce.domain.agent import AgentRole, AgentState
from sona_workforce.domain.models import AgentResult, AgentTask
from sona_workforce.infrastructure.agent_registry import AgentRegistry
from sona_workforce.infrastructure.agents.base_agent import BaseAgent

logger = structlog.get_logger()

_DELEGATION_HIERARCHY: dict[AgentRole, list[AgentRole]] = {
    AgentRole.MANAGER: [AgentRole.WORKER, AgentRole.SPECIALIST, AgentRole.REVIEWER],
    AgentRole.SPECIALIST: [AgentRole.WORKER],
    AgentRole.REVIEWER: [AgentRole.WORKER],
    AgentRole.WORKER: [],
}


@dataclass
class DelegationResult:
    """Result of a delegation operation."""

    success: bool
    from_agent: str
    to_agent: str
    task_id: str
    result: AgentResult | None = None
    error: str = ""
    chain: list[str] = field(default_factory=list)


class DelegationEngine:
    """Hierarchical delegation engine for agent-to-agent task delegation.

    Supports: Manager -> Worker -> Specialist delegation paths.
    Recursive delegation with configurable depth limit.
    Can split complex tasks into subtasks.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        agents: dict[str, BaseAgent],
        max_depth: int = 3,
    ) -> None:
        self._registry = registry
        self._agents = agents
        self._max_depth = max_depth
        self._delegation_count = 0

    async def delegate(
        self,
        from_agent_id: str,
        task: AgentTask,
        depth: int = 0,
    ) -> DelegationResult:
        """Delegate a task from one agent to an appropriate subordinate.

        Uses hierarchical delegation: Manager -> Worker/Specialist.
        Enforces max depth to prevent infinite delegation loops.
        """
        if depth >= self._max_depth:
            return DelegationResult(
                success=False,
                from_agent=from_agent_id,
                to_agent="",
                task_id=task.task_id,
                error=f"Max delegation depth ({self._max_depth}) reached",
            )

        from_profile = self._registry.get(from_agent_id)
        if from_profile is None:
            return DelegationResult(
                success=False,
                from_agent=from_agent_id,
                to_agent="",
                task_id=task.task_id,
                error=f"Agent {from_agent_id} not found",
            )

        # Find eligible delegates based on hierarchy
        allowed_roles = _DELEGATION_HIERARCHY.get(from_profile.role, [])
        if not allowed_roles:
            return DelegationResult(
                success=False,
                from_agent=from_agent_id,
                to_agent="",
                task_id=task.task_id,
                error=f"Agent role {from_profile.role} cannot delegate",
            )

        # Find available agent to delegate to
        delegate = self._find_delegate(task, allowed_roles)
        if delegate is None:
            return DelegationResult(
                success=False,
                from_agent=from_agent_id,
                to_agent="",
                task_id=task.task_id,
                error="No available delegate found",
            )

        # Execute delegation
        delegate_agent = self._agents.get(delegate.agent_id)
        if delegate_agent is None:
            return DelegationResult(
                success=False,
                from_agent=from_agent_id,
                to_agent=delegate.agent_id,
                task_id=task.task_id,
                error=f"Agent instance {delegate.agent_id} not available",
            )

        self._delegation_count += 1
        await logger.ainfo(
            "task_delegated",
            from_agent=from_agent_id,
            to_agent=delegate.agent_id,
            task_id=task.task_id,
            depth=depth,
        )

        result = await delegate_agent.process(task)
        chain = [from_agent_id, delegate.agent_id]

        return DelegationResult(
            success=result.status == "success",
            from_agent=from_agent_id,
            to_agent=delegate.agent_id,
            task_id=task.task_id,
            result=result,
            chain=chain,
        )

    def _find_delegate(
        self,
        task: AgentTask,
        allowed_roles: list[AgentRole],
    ) -> Any:
        """Find the best delegate for a task among allowed roles."""
        # First try type match with allowed roles
        type_agents = self._registry.get_by_type(task.agent_type)
        for agent in type_agents:
            if (
                agent.role in allowed_roles
                and agent.state in (AgentState.IDLE, AgentState.PROCESSING)
                and agent.active_tasks < agent.max_concurrent_tasks
            ):
                return agent

        # Fallback: any agent with allowed role and capacity
        for role in allowed_roles:
            role_agents = self._registry.get_by_role(role)
            for agent in role_agents:
                if (
                    agent.state in (AgentState.IDLE, AgentState.PROCESSING)
                    and agent.active_tasks < agent.max_concurrent_tasks
                ):
                    return agent

        return None

    async def split_and_delegate(
        self,
        from_agent_id: str,
        task: AgentTask,
        subtask_instructions: list[str],
    ) -> list[DelegationResult]:
        """Split a task into subtasks and delegate each."""
        results: list[DelegationResult] = []
        for i, instruction in enumerate(subtask_instructions):
            subtask = AgentTask(
                task_id=f"{task.task_id}-sub-{i}",
                agent_type=task.agent_type,
                instruction=instruction,
                context=task.context,
                timeout_seconds=task.timeout_seconds,
                priority=task.priority,
            )
            result = await self.delegate(from_agent_id, subtask)
            results.append(result)
        return results

    @property
    def delegation_count(self) -> int:
        """Total number of delegations performed."""
        return self._delegation_count

    def get_stats(self) -> dict[str, Any]:
        """Get delegation engine statistics."""
        return {
            "total_delegations": self._delegation_count,
            "max_depth": self._max_depth,
        }
