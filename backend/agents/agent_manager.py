"""Central agent manager — orchestrates the multi-agent system."""

from __future__ import annotations

from typing import Any

from agents.agent_coordinator import AgentCoordinator
from agents.agent_executor import AgentExecutor
from agents.agent_factory import AgentFactory
from agents.agent_registry import AgentRegistry
from agents.agent_supervisor import AgentSupervisor
from agents.exceptions import AgentNotFoundError
from agents.schemas import (
    Agent,
    AgentState,
    AgentTask,
    AgentType,
    CoordinationPlan,
)
from config.logging import get_logger

logger = get_logger(__name__)


class AgentManager:
    """Central orchestrator for the multi-agent system."""

    def __init__(
        self,
        registry: AgentRegistry,
        factory: AgentFactory,
        coordinator: AgentCoordinator,
        executor: AgentExecutor,
        supervisor: AgentSupervisor,
    ) -> None:
        self._registry = registry
        self._factory = factory
        self._coordinator = coordinator
        self._executor = executor
        self._supervisor = supervisor

    async def create_agent(
        self,
        name: str,
        agent_type: AgentType,
        capabilities: list[str] | None = None,
    ) -> Agent:
        """Create and register a new agent."""
        agent = self._factory.create(name=name, agent_type=agent_type, capabilities=capabilities)
        self._registry.register(agent)
        logger.info("agent_created_via_manager", agent_id=agent.agent_id, name=name)
        return agent

    async def terminate_agent(self, agent_id: str) -> bool:
        """Terminate and deregister an agent."""
        agent = self._registry.get(agent_id)
        if agent is None:
            return False
        agent.state = AgentState.TERMINATED
        self._registry.deregister(agent_id)
        logger.info("agent_terminated", agent_id=agent_id)
        return True

    async def assign_task(
        self, agent_id: str, description: str, params: dict[str, Any] | None = None
    ) -> AgentTask:
        """Assign a task to an agent."""
        agent = self._registry.get(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id=agent_id)
        task = AgentTask(description=description, agent_id=agent_id, params=params or {})
        agent.state = AgentState.ASSIGNED
        return task

    async def execute_plan(self, plan: CoordinationPlan) -> dict[str, Any]:
        """Execute a coordination plan."""
        tasks = [AgentTask(description=tid) for tid in plan.tasks]
        return await self._coordinator.coordinate(plan, tasks)

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get an agent by ID."""
        return self._registry.get(agent_id)

    def list_agents(self, state: AgentState | None = None) -> list[Agent]:
        """List agents, optionally filtered by state."""
        if state is not None:
            return self._registry.list_by_state(state)
        return self._registry.list_all()

    def get_status(self) -> dict[str, Any]:
        """Get the overall agent system status."""
        return {
            "total_agents": self._registry.count,
            "registry_stats": self._registry.get_stats(),
            "supervised": self._supervisor.get_supervised(),
        }
