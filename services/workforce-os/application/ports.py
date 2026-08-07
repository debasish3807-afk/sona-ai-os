"""Abstract port interfaces for the Workforce OS service.

Defines the contracts that infrastructure adapters must implement
to provide agent execution and coordination capabilities.
"""

from abc import ABC, abstractmethod

from domain.models import AgentResult, AgentStatus, AgentTask, AgentType


class AgentPort(ABC):
    """Port for individual agent implementation.

    Each specialized agent (coding, research, planner, etc.) implements
    this interface to provide its processing capabilities to the system.
    Concrete adapters handle LLM interactions, tool use, and domain logic.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent resources.

        Sets up any connections, loads configurations, and prepares
        the agent for processing tasks. Must be called before process().
        """
        ...

    @abstractmethod
    async def process(self, task: AgentTask) -> AgentResult:
        """Process an assigned task.

        Executes the given task using this agent's specialized capabilities
        and returns the result. May involve LLM calls, tool use, or
        multi-step reasoning.

        Args:
            task: The agent task to process.

        Returns:
            An AgentResult containing the output and execution metadata.
        """
        ...

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """Return list of capabilities this agent provides.

        Used for agent discovery and task routing to determine
        which agents can handle specific types of work.

        Returns:
            A list of capability identifiers this agent supports.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check agent health.

        Verifies that the agent is operational and ready to accept tasks.
        Checks connections, model availability, and internal state.

        Returns:
            True if the agent is healthy and ready, False otherwise.
        """
        ...


class AgentCoordinatorPort(ABC):
    """Port for agent coordination and dispatch.

    Manages the lifecycle and task routing for all registered agents.
    Handles dispatch decisions, parallel execution, agent registration,
    and status monitoring.
    """

    @abstractmethod
    async def dispatch(self, task: AgentTask) -> AgentResult:
        """Dispatch task to the most suitable agent.

        Routes the task to an appropriate agent based on agent_type,
        availability, and current load. Handles failover if the
        primary agent is unavailable.

        Args:
            task: The agent task to dispatch.

        Returns:
            The result from the agent that processed the task.
        """
        ...

    @abstractmethod
    async def dispatch_parallel(self, tasks: list[AgentTask]) -> list[AgentResult]:
        """Dispatch multiple tasks in parallel.

        Sends multiple tasks to their respective agents concurrently
        and collects all results. Useful for multi-agent collaboration
        on complex problems.

        Args:
            tasks: List of agent tasks to execute in parallel.

        Returns:
            List of results corresponding to each dispatched task.
        """
        ...

    @abstractmethod
    async def register_agent(self, agent_type: AgentType, agent: AgentPort) -> None:
        """Register a new agent instance.

        Adds an agent to the coordinator's registry, making it
        available for task dispatch. The agent should already be
        initialized before registration.

        Args:
            agent_type: The type classification for this agent.
            agent: The agent instance to register.
        """
        ...

    @abstractmethod
    async def list_agents(self) -> dict[AgentType, AgentStatus]:
        """List all agents and their current status.

        Returns the registry of all registered agents with their
        current operational status for monitoring and routing decisions.

        Returns:
            A mapping of agent types to their current status.
        """
        ...
