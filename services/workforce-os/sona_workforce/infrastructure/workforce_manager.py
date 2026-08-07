"""Workforce Manager - top-level orchestrator implementing AgentCoordinatorPort."""

from __future__ import annotations

from typing import Any

import structlog

from sona_workforce.application.ports import AgentCoordinatorPort, AgentPort
from sona_workforce.domain.agent import AgentState
from sona_workforce.domain.models import AgentResult, AgentStatus, AgentTask, AgentType
from sona_workforce.infrastructure.agent_registry import AgentRegistry
from sona_workforce.infrastructure.agent_runtime import AgentRuntime
from sona_workforce.infrastructure.agent_scheduler import AgentScheduler
from sona_workforce.infrastructure.agents.base_agent import BaseAgent
from sona_workforce.infrastructure.communication_bus import CommunicationBus
from sona_workforce.infrastructure.delegation_engine import DelegationEngine
from sona_workforce.infrastructure.health_monitor import HealthMonitor
from sona_workforce.infrastructure.metrics import WorkforceMetrics

logger = structlog.get_logger()


class WorkforceManager(AgentCoordinatorPort):
    """Top-level orchestrator for the Workforce OS.

    Integrates: registry + scheduler + runtime + delegation + communication + health + metrics.
    Implements the AgentCoordinatorPort interface.
    """

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        metrics: WorkforceMetrics | None = None,
    ) -> None:
        self._registry = registry or AgentRegistry()
        self._metrics = metrics or WorkforceMetrics()
        self._agents: dict[str, BaseAgent] = {}

        # Build the subsystems
        self._scheduler = AgentScheduler(self._registry)
        self._runtime = AgentRuntime(self._registry)
        self._communication = CommunicationBus()
        self._delegation = DelegationEngine(self._registry, self._agents)
        self._health_monitor = HealthMonitor(self._registry, self._agents)

    @property
    def registry(self) -> AgentRegistry:
        """Access the agent registry."""
        return self._registry

    @property
    def scheduler(self) -> AgentScheduler:
        """Access the agent scheduler."""
        return self._scheduler

    @property
    def runtime(self) -> AgentRuntime:
        """Access the agent runtime."""
        return self._runtime

    @property
    def communication(self) -> CommunicationBus:
        """Access the communication bus."""
        return self._communication

    @property
    def delegation(self) -> DelegationEngine:
        """Access the delegation engine."""
        return self._delegation

    @property
    def health_monitor(self) -> HealthMonitor:
        """Access the health monitor."""
        return self._health_monitor

    @property
    def metrics(self) -> WorkforceMetrics:
        """Access workforce metrics."""
        return self._metrics

    async def register_agent(self, agent_type: AgentType, agent: AgentPort) -> None:
        """Register a new agent instance.

        Adds the agent to registry, runtime, communication bus, and initializes it.
        """
        if not isinstance(agent, BaseAgent):
            raise TypeError("Agent must be a BaseAgent instance")

        base_agent = agent
        agent_id = base_agent.agent_id

        # Initialize the agent
        await base_agent.initialize()

        # Register in all subsystems
        await self._registry.register(base_agent.profile)
        self._runtime.register_agent_instance(base_agent)
        self._agents[agent_id] = base_agent
        self._communication.register_agent(agent_id)

        await logger.ainfo(
            "agent_registered_in_workforce",
            agent_id=agent_id,
            agent_type=agent_type,
        )

    async def dispatch(self, task: AgentTask) -> AgentResult:
        """Dispatch task to the most suitable agent.

        Routes based on scheduler selection. Falls back to delegation if needed.
        """
        # Update queue metrics
        self._metrics.update_queue_depth(self._scheduler.queue_depth)

        # Select best agent via scheduler
        selected = await self._scheduler.select_agent(task)
        if selected is None:
            # Try queuing for later
            self._scheduler.enqueue(task)
            self._metrics.update_queue_depth(self._scheduler.queue_depth)
            return AgentResult(
                task_id=task.task_id,
                agent_type=AgentType(task.agent_type),
                output="",
                status="queued",
            )

        # Execute via runtime
        self._scheduler.mark_processing(selected.agent_id, task)
        self._metrics.update_active_count(self._scheduler.active_count)

        result = await self._runtime.execute(selected.agent_id, task)

        self._scheduler.mark_completed(selected.agent_id)
        self._metrics.update_active_count(self._scheduler.active_count)

        # Record metrics
        if result.status == "success":
            self._metrics.record_task_completion(
                agent_id=selected.agent_id,
                duration_ms=result.duration_ms,
                tokens_used=result.tokens_used,
            )
        else:
            self._metrics.record_task_failure(
                agent_id=selected.agent_id,
                duration_ms=result.duration_ms,
            )

        return result

    async def dispatch_parallel(self, tasks: list[AgentTask]) -> list[AgentResult]:
        """Dispatch multiple tasks in parallel."""
        assignments: list[tuple[str, AgentTask]] = []

        for task in tasks:
            selected = await self._scheduler.select_agent(task)
            if selected:
                assignments.append((selected.agent_id, task))
                self._scheduler.mark_processing(selected.agent_id, task)
            else:
                # Queue tasks that cannot be assigned
                self._scheduler.enqueue(task)

        self._metrics.update_active_count(self._scheduler.active_count)

        if not assignments:
            return [
                AgentResult(
                    task_id=t.task_id,
                    agent_type=AgentType(t.agent_type),
                    output="",
                    status="queued",
                )
                for t in tasks
            ]

        results = await self._runtime.execute_parallel(assignments)

        # Update metrics and scheduler
        for (agent_id, _), result in zip(assignments, results, strict=True):
            self._scheduler.mark_completed(agent_id)
            if result.status == "success":
                self._metrics.record_task_completion(
                    agent_id=agent_id,
                    duration_ms=result.duration_ms,
                    tokens_used=result.tokens_used,
                )
            else:
                self._metrics.record_task_failure(
                    agent_id=agent_id,
                    duration_ms=result.duration_ms,
                )

        self._metrics.update_active_count(self._scheduler.active_count)
        return results

    async def list_agents(self) -> dict[AgentType, AgentStatus]:
        """List all agents and their current status."""
        result: dict[AgentType, AgentStatus] = {}
        for profile in self._registry.all_agents():
            agent_type = AgentType(profile.agent_type)
            state = profile.state
            if state == AgentState.IDLE:
                status = AgentStatus.IDLE
            elif state in (AgentState.PROCESSING, AgentState.DELEGATING):
                status = AgentStatus.BUSY
            elif state == AgentState.ERROR:
                status = AgentStatus.ERROR
            else:
                status = AgentStatus.STOPPED
            result[agent_type] = status
        return result

    async def health_check_all(self) -> dict[str, Any]:
        """Run health checks on all agents."""
        return {
            agent_id: status.healthy
            for agent_id, status in (await self._health_monitor.check_all()).items()
        }

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive workforce statistics."""
        return {
            "metrics": self._metrics.get_summary(),
            "scheduler": self._scheduler.get_stats(),
            "runtime": self._runtime.get_stats(),
            "health": self._health_monitor.get_stats(),
            "communication": self._communication.get_stats(),
            "delegation": self._delegation.get_stats(),
        }
