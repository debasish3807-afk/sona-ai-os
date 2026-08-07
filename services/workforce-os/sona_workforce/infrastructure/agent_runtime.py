"""Agent Runtime - executes tasks on agents with lifecycle management."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agent_registry import AgentRegistry
from sona_workforce.infrastructure.agents.base_agent import BaseAgent

logger = structlog.get_logger()


class AgentRuntime:
    """Executes tasks on agents with timeout, retry, and error handling.

    Manages the lifecycle: dispatch -> execute -> collect result -> update metrics.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        max_retries: int = 2,
        default_timeout: float = 120.0,
    ) -> None:
        self._registry = registry
        self._max_retries = max_retries
        self._default_timeout = default_timeout
        self._agents: dict[str, BaseAgent] = {}
        self._execution_count = 0
        self._failure_count = 0

    def register_agent_instance(self, agent: BaseAgent) -> None:
        """Register a concrete agent instance for execution."""
        self._agents[agent.agent_id] = agent

    def get_agent_instance(self, agent_id: str) -> BaseAgent | None:
        """Get a registered agent instance by ID."""
        return self._agents.get(agent_id)

    async def execute(
        self,
        agent_id: str,
        task: AgentTask,
        timeout: float | None = None,
    ) -> AgentResult:
        """Execute a task on a specific agent with timeout and retry."""
        agent = self._agents.get(agent_id)
        if agent is None:
            return AgentResult(
                task_id=task.task_id,
                agent_type=AgentType(task.agent_type),
                output="",
                status="error",
            )

        effective_timeout = timeout or task.timeout_seconds or self._default_timeout
        retries_left = self._max_retries

        while retries_left >= 0:
            try:
                result = await asyncio.wait_for(
                    agent.process(task),
                    timeout=effective_timeout,
                )
                self._execution_count += 1

                if result.status == "error" and retries_left > 0:
                    retries_left -= 1
                    await logger.awarning(
                        "task_retry",
                        agent_id=agent_id,
                        task_id=task.task_id,
                        retries_left=retries_left,
                    )
                    continue

                if result.status == "error":
                    self._failure_count += 1

                return result

            except TimeoutError:
                retries_left -= 1
                await logger.awarning(
                    "task_timeout",
                    agent_id=agent_id,
                    task_id=task.task_id,
                    timeout=effective_timeout,
                    retries_left=retries_left,
                )
                if retries_left < 0:
                    self._failure_count += 1
                    return AgentResult(
                        task_id=task.task_id,
                        agent_type=AgentType(task.agent_type),
                        output="",
                        status="timeout",
                    )

            except Exception as exc:
                self._failure_count += 1
                await logger.aerror(
                    "task_execution_error",
                    agent_id=agent_id,
                    task_id=task.task_id,
                    error=str(exc),
                )
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=AgentType(task.agent_type),
                    output="",
                    status="error",
                )

        # Should not reach here, but safety fallback
        self._failure_count += 1
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType(task.agent_type),
            output="",
            status="error",
        )

    async def execute_parallel(
        self,
        assignments: list[tuple[str, AgentTask]],
    ) -> list[AgentResult]:
        """Execute multiple tasks in parallel on their assigned agents."""
        coros = [self.execute(agent_id, task) for agent_id, task in assignments]
        return list(await asyncio.gather(*coros))

    def get_stats(self) -> dict[str, Any]:
        """Get runtime statistics."""
        return {
            "total_executions": self._execution_count,
            "total_failures": self._failure_count,
            "registered_agents": len(self._agents),
        }
