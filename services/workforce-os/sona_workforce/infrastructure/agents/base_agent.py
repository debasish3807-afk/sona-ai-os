"""Base agent implementation with shared logic."""

from __future__ import annotations

import time
from abc import abstractmethod
from typing import Any

import structlog

from sona_workforce.application.ports import AgentPort
from sona_workforce.domain.agent import (
    AgentCapability,
    AgentProfile,
    AgentRole,
    AgentState,
)
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType

logger = structlog.get_logger()


class BaseAgent(AgentPort):
    """Abstract base agent providing shared logic for all agent implementations.

    Provides state management, metric recording, timeout handling, and health checks.
    All specialized agents extend this class.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: AgentType,
        role: AgentRole,
        capabilities: list[AgentCapability],
        max_concurrent_tasks: int = 3,
        priority: int = 5,
    ) -> None:
        self._profile = AgentProfile(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type.value,
            role=role,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent_tasks,
            priority=priority,
        )
        self._initialized = False
        self._healthy = True
        self._metrics: dict[str, Any] = {
            "total_processed": 0,
            "total_failed": 0,
            "total_tokens": 0,
            "total_duration_ms": 0.0,
        }

    @property
    def profile(self) -> AgentProfile:
        """Get the agent's profile."""
        return self._profile

    @property
    def agent_id(self) -> str:
        """Get the agent's unique ID."""
        return self._profile.agent_id

    @property
    def agent_type(self) -> str:
        """Get the agent's type."""
        return self._profile.agent_type

    @property
    def state(self) -> AgentState:
        """Get the agent's current state."""
        return self._profile.state

    @property
    def metrics(self) -> dict[str, Any]:
        """Get the agent's metrics."""
        return self._metrics.copy()

    def _set_state(self, state: AgentState) -> None:
        """Update the agent's state."""
        self._profile.state = state

    async def initialize(self) -> None:
        """Initialize agent resources."""
        self._set_state(AgentState.INITIALIZING)
        self._initialized = True
        self._set_state(AgentState.IDLE)
        await logger.ainfo("agent_initialized", agent_id=self.agent_id)

    async def process(self, task: AgentTask) -> AgentResult:
        """Process a task with state management and metrics tracking."""
        self._set_state(AgentState.PROCESSING)
        self._profile.active_tasks += 1
        start_time = time.monotonic()

        try:
            result = await self._execute(task)
            duration_ms = (time.monotonic() - start_time) * 1000

            # Update metrics
            self._metrics["total_processed"] += 1
            self._metrics["total_tokens"] += result.tokens_used
            self._metrics["total_duration_ms"] += duration_ms
            self._profile.total_completed += 1

            await logger.ainfo(
                "task_completed",
                agent_id=self.agent_id,
                task_id=task.task_id,
                duration_ms=duration_ms,
            )

            return AgentResult(
                task_id=result.task_id,
                agent_type=result.agent_type,
                output=result.output,
                status=result.status,
                tokens_used=result.tokens_used,
                duration_ms=duration_ms,
                artifacts=result.artifacts,
            )
        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            self._metrics["total_failed"] += 1
            self._profile.total_failed += 1
            self._set_state(AgentState.ERROR)

            await logger.aerror(
                "task_failed",
                agent_id=self.agent_id,
                task_id=task.task_id,
                error=str(exc),
            )

            return AgentResult(
                task_id=task.task_id,
                agent_type=AgentType(task.agent_type),
                output="",
                status="error",
                duration_ms=duration_ms,
            )
        finally:
            self._profile.active_tasks -= 1
            if self._profile.state != AgentState.ERROR:
                self._set_state(AgentState.IDLE)

    @abstractmethod
    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute the task-specific logic. Subclasses must implement."""
        ...

    async def get_capabilities(self) -> list[str]:
        """Return list of capabilities this agent provides."""
        return [cap.value for cap in self._profile.capabilities]

    async def health_check(self) -> bool:
        """Check if the agent is healthy."""
        return self._healthy and self._profile.state != AgentState.ERROR

    async def shutdown(self) -> None:
        """Gracefully shut down the agent."""
        self._set_state(AgentState.SHUTDOWN)
        self._initialized = False
        await logger.ainfo("agent_shutdown", agent_id=self.agent_id)
