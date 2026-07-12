"""Agent system manager.

Top-level orchestrator for the multi-agent framework. Integrates
the registry, lifecycle, router, coordinator, executor, and
workflow engine into a unified management interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

from agents.base import BaseAgent
from agents.capabilities import CapabilityRequirement
from agents.context import ExecutionContext, ExecutionResult
from agents.coordinator import AgentCoordinator, DelegationRequest, DelegationResult
from agents.executor import AgentExecutor
from agents.factory import AgentFactory
from agents.lifecycle import AgentLifecycleManager
from agents.registry import AgentRegistry
from agents.router import AgentRouter
from agents.state import AgentState, AgentStatus
from agents.workflow import WorkflowEngine


@dataclass
class AgentManagerConfig:
    """Configuration for the agent system manager.

    Attributes:
        auto_discover: Auto-discover registered agent plugins.
        auto_start: Start all agents on initialization.
        max_concurrent_agents: Maximum agents running concurrently.
        health_check_interval_seconds: Health check frequency.
        default_timeout_seconds: Default task timeout.
        enable_workflows: Enable workflow engine.
        metadata: Additional configuration.
    """

    auto_discover: bool = True
    auto_start: bool = True
    max_concurrent_agents: int = 50
    health_check_interval_seconds: int = 30
    default_timeout_seconds: float = 120.0
    enable_workflows: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)



class AgentManager(ABC):
    """Abstract interface for the agent system manager.

    Provides a unified API for interacting with the multi-agent
    framework including task execution, agent management, and
    system monitoring.
    """

    @property
    @abstractmethod
    def registry(self) -> AgentRegistry:
        """Access the agent registry."""
        ...

    @property
    @abstractmethod
    def lifecycle(self) -> AgentLifecycleManager:
        """Access the lifecycle manager."""
        ...

    @property
    @abstractmethod
    def router(self) -> AgentRouter:
        """Access the task router."""
        ...

    @property
    @abstractmethod
    def coordinator(self) -> AgentCoordinator:
        """Access the multi-agent coordinator."""
        ...

    @property
    @abstractmethod
    def executor(self) -> AgentExecutor:
        """Access the task executor."""
        ...

    @property
    @abstractmethod
    def workflow_engine(self) -> WorkflowEngine:
        """Access the workflow engine."""
        ...

    @property
    @abstractmethod
    def factory(self) -> AgentFactory:
        """Access the agent factory."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def initialize(
        self, config: Optional[AgentManagerConfig] = None
    ) -> None:
        """Initialize the agent system.

        Discovers agents, resolves dependencies, and starts
        agents according to configuration.

        Args:
            config: Optional configuration override.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the agent system gracefully."""
        ...

    # ------------------------------------------------------------------
    # Task Execution
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(
        self,
        context: ExecutionContext,
        agent_id: Optional[str] = None,
        requirements: Optional[CapabilityRequirement] = None,
    ) -> ExecutionResult:
        """Execute a task with automatic agent selection.

        Routes to the best agent and executes the task.

        Args:
            context: Execution context with task details.
            agent_id: Optional explicit agent selection.
            requirements: Optional capability requirements.

        Returns:
            ExecutionResult from the selected agent.
        """
        ...

    @abstractmethod
    async def execute_stream(
        self,
        context: ExecutionContext,
        agent_id: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Execute a task with streaming output.

        Args:
            context: Execution context.
            agent_id: Optional agent selection.

        Yields:
            Incremental result chunks.
        """
        ...

    @abstractmethod
    async def delegate(
        self, request: DelegationRequest
    ) -> DelegationResult:
        """Delegate a task between agents.

        Args:
            request: The delegation request.

        Returns:
            DelegationResult with outcome.
        """
        ...

    # ------------------------------------------------------------------
    # Agent Management
    # ------------------------------------------------------------------

    @abstractmethod
    async def add_agent(
        self, agent: BaseAgent, priority: int = 50
    ) -> str:
        """Add and start a new agent.

        Args:
            agent: The agent to add.
            priority: Selection priority.

        Returns:
            The agent_id.
        """
        ...

    @abstractmethod
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the system.

        Args:
            agent_id: The agent to remove.

        Returns:
            True if removed.
        """
        ...

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID.

        Args:
            agent_id: The agent identifier.

        Returns:
            BaseAgent or None.
        """
        ...

    @abstractmethod
    async def list_agents(self) -> List[AgentState]:
        """List all agents with their current state.

        Returns:
            List of agent states.
        """
        ...

    @abstractmethod
    async def get_available_agents(self) -> List[str]:
        """Get IDs of currently available agents.

        Returns:
            List of available agent IDs.
        """
        ...

    # ------------------------------------------------------------------
    # Monitoring
    # ------------------------------------------------------------------

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Run system-wide health check.

        Returns:
            Health status for all agents.
        """
        ...

    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics.

        Returns:
            Aggregated metrics from all agents.
        """
        ...
