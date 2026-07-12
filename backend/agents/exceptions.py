"""Agent-specific exception hierarchy.

Defines structured exceptions for all agent operations including
lifecycle failures, communication errors, execution issues, and
coordination problems.
"""

from typing import Any


class AgentError(Exception):
    """Base exception for all agent-related errors.

    Attributes:
        message: Human-readable error description.
        agent_id: The agent that raised the error.
        error_code: Machine-readable error code.
        details: Additional error context.
        retryable: Whether the operation can be retried.
    """

    def __init__(
        self,
        message: str = "Agent error occurred",
        agent_id: str | None = None,
        error_code: str = "AGENT_ERROR",
        details: dict[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        self.message = message
        self.agent_id = agent_id
        self.error_code = error_code
        self.details = details or {}
        self.retryable = retryable
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "agent_id": self.agent_id,
            "retryable": self.retryable,
            "details": self.details,
        }


class AgentNotFoundError(AgentError):
    """Requested agent does not exist in the registry."""

    def __init__(
        self,
        message: str = "Agent not found",
        agent_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            agent_id=agent_id,
            error_code="AGENT_NOT_FOUND",
            details=details,
            retryable=False,
        )


class AgentInitializationError(AgentError):
    """Agent failed to initialize."""

    def __init__(
        self,
        message: str = "Agent initialization failed",
        agent_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            agent_id=agent_id,
            error_code="AGENT_INIT_FAILED",
            details=details,
            retryable=True,
        )


class AgentExecutionError(AgentError):
    """Agent failed during task execution."""

    def __init__(
        self,
        message: str = "Agent execution failed",
        agent_id: str | None = None,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if task_id:
            _details["task_id"] = task_id
        super().__init__(
            message=message,
            agent_id=agent_id,
            error_code="AGENT_EXECUTION_FAILED",
            details=_details,
            retryable=True,
        )


class AgentTimeoutError(AgentError):
    """Agent operation timed out."""

    def __init__(
        self,
        message: str = "Agent operation timed out",
        agent_id: str | None = None,
        timeout_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if timeout_seconds is not None:
            _details["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            agent_id=agent_id,
            error_code="AGENT_TIMEOUT",
            details=_details,
            retryable=True,
        )


class AgentCommunicationError(AgentError):
    """Inter-agent communication failure."""

    def __init__(
        self,
        message: str = "Agent communication failed",
        source_agent: str | None = None,
        target_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if source_agent:
            _details["source_agent"] = source_agent
        if target_agent:
            _details["target_agent"] = target_agent
        super().__init__(
            message=message,
            agent_id=source_agent,
            error_code="AGENT_COMMUNICATION_FAILED",
            details=_details,
            retryable=True,
        )


class AgentDependencyError(AgentError):
    """Agent dependency is unavailable."""

    def __init__(
        self,
        message: str = "Agent dependency unavailable",
        agent_id: str | None = None,
        missing_dependencies: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if missing_dependencies:
            _details["missing_dependencies"] = missing_dependencies
        super().__init__(
            message=message,
            agent_id=agent_id,
            error_code="AGENT_DEPENDENCY_ERROR",
            details=_details,
            retryable=True,
        )


class AgentCapabilityError(AgentError):
    """Agent does not have the required capability."""

    def __init__(
        self,
        message: str = "Agent lacks required capability",
        agent_id: str | None = None,
        required_capability: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if required_capability:
            _details["required_capability"] = required_capability
        super().__init__(
            message=message,
            agent_id=agent_id,
            error_code="AGENT_CAPABILITY_ERROR",
            details=_details,
            retryable=False,
        )


class WorkflowError(AgentError):
    """Workflow execution error."""

    def __init__(
        self,
        message: str = "Workflow execution failed",
        workflow_id: str | None = None,
        step_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if workflow_id:
            _details["workflow_id"] = workflow_id
        if step_id:
            _details["step_id"] = step_id
        super().__init__(
            message=message,
            error_code="WORKFLOW_ERROR",
            details=_details,
            retryable=True,
        )


class CoordinationError(AgentError):
    """Multi-agent coordination failure."""

    def __init__(
        self,
        message: str = "Agent coordination failed",
        involved_agents: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = details or {}
        if involved_agents:
            _details["involved_agents"] = involved_agents
        super().__init__(
            message=message,
            error_code="COORDINATION_ERROR",
            details=_details,
            retryable=True,
        )
