"""Agent exception hierarchy for the multi-agent coordination fabric."""

from __future__ import annotations

from config.logging import get_logger

logger = get_logger(__name__)


class AgentError(Exception):
    """Base exception for all agent-related errors."""

    def __init__(self, message: str = "Agent error occurred", agent_id: str = "") -> None:
        self.message = message
        self.agent_id = agent_id
        super().__init__(self.message)


class AgentNotFoundError(AgentError):
    """Requested agent does not exist."""

    def __init__(self, message: str = "Agent not found", agent_id: str = "") -> None:
        super().__init__(message=message, agent_id=agent_id)


class AgentCreationError(AgentError):
    """Agent could not be created."""

    def __init__(self, message: str = "Agent creation failed", agent_id: str = "") -> None:
        super().__init__(message=message, agent_id=agent_id)


class AgentTimeoutError(AgentError):
    """Agent operation timed out."""

    def __init__(self, message: str = "Agent operation timed out", agent_id: str = "") -> None:
        super().__init__(message=message, agent_id=agent_id)


class CoordinationError(AgentError):
    """Multi-agent coordination failure."""

    def __init__(self, message: str = "Coordination failed", agent_id: str = "") -> None:
        super().__init__(message=message, agent_id=agent_id)


class ConsensusError(AgentError):
    """Consensus could not be reached."""

    def __init__(self, message: str = "Consensus not reached", agent_id: str = "") -> None:
        super().__init__(message=message, agent_id=agent_id)


class DelegationError(AgentError):
    """Task delegation failure."""

    def __init__(self, message: str = "Delegation failed", agent_id: str = "") -> None:
        super().__init__(message=message, agent_id=agent_id)


class AgentSecurityError(AgentError):
    """Security violation by an agent."""

    def __init__(self, message: str = "Security violation", agent_id: str = "") -> None:
        super().__init__(message=message, agent_id=agent_id)
