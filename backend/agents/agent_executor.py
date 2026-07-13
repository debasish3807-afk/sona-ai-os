"""Executes agent tasks."""

from __future__ import annotations

import time

from agents.agent_context import AgentContext
from agents.agent_lifecycle import AgentLifecycle
from agents.schemas import Agent, AgentState, AgentTask
from config.logging import get_logger

logger = get_logger(__name__)


class AgentExecutor:
    """Executes tasks assigned to agents."""

    def __init__(self, lifecycle: AgentLifecycle) -> None:
        self._lifecycle = lifecycle

    async def execute(self, agent: Agent, task: AgentTask, context: AgentContext) -> AgentTask:
        """Execute a single task with the given agent."""
        return await self._execute_single(agent, task, context)

    async def execute_batch(self, assignments: list[tuple[Agent, AgentTask]]) -> list[AgentTask]:
        """Execute a batch of agent-task assignments."""
        results: list[AgentTask] = []
        for agent, task in assignments:
            ctx = AgentContext(agent_id=agent.agent_id, task_id=task.task_id)
            result = await self._execute_single(agent, task, ctx)
            results.append(result)
        return results

    async def _execute_single(
        self, agent: Agent, task: AgentTask, context: AgentContext
    ) -> AgentTask:
        """Internal execution of a single task."""
        start_time = time.time()
        # Transition agent to running
        self._lifecycle.transition(agent, AgentState.RUNNING)
        task.state = AgentState.RUNNING
        context.set("start_time", start_time)

        try:
            # Simulate task execution
            task.result = {"status": "completed", "agent_id": agent.agent_id}
            task.state = AgentState.COMPLETED
            task.completed_at = time.time()
            self._lifecycle.transition(agent, AgentState.COMPLETED)
            logger.info(
                "task_executed",
                agent_id=agent.agent_id,
                task_id=task.task_id,
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception as exc:
            task.state = AgentState.FAILED
            task.result = {"error": str(exc)}
            self._lifecycle.transition(agent, AgentState.FAILED)
            logger.error("task_execution_failed", agent_id=agent.agent_id, error=str(exc))

        return task
