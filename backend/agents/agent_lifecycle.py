"""Agent lifecycle state machine."""

from __future__ import annotations

from agents.schemas import Agent, AgentState
from config.logging import get_logger

logger = get_logger(__name__)

# Valid state transitions
_TRANSITIONS: dict[AgentState, list[AgentState]] = {
    AgentState.CREATED: [AgentState.INITIALIZING],
    AgentState.INITIALIZING: [AgentState.IDLE],
    AgentState.IDLE: [AgentState.ASSIGNED],
    AgentState.ASSIGNED: [AgentState.RUNNING],
    AgentState.RUNNING: [AgentState.PAUSED, AgentState.COMPLETED, AgentState.FAILED],
    AgentState.PAUSED: [AgentState.RUNNING, AgentState.TERMINATED],
    AgentState.COMPLETED: [AgentState.TERMINATED, AgentState.IDLE],
    AgentState.FAILED: [AgentState.TERMINATED, AgentState.IDLE],
    AgentState.TERMINATED: [],
}


class AgentLifecycle:
    """Manages agent state transitions."""

    def __init__(self) -> None:
        self._transitions = _TRANSITIONS

    def transition(self, agent: Agent, target_state: AgentState) -> bool:
        """Transition an agent to a new state if valid."""
        if not self.can_transition(agent.state, target_state):
            logger.warning(
                "invalid_transition",
                agent_id=agent.agent_id,
                current=agent.state.value,
                target=target_state.value,
            )
            return False
        agent.state = target_state
        logger.debug(
            "agent_state_changed",
            agent_id=agent.agent_id,
            new_state=target_state.value,
        )
        return True

    def can_transition(self, current: AgentState, target: AgentState) -> bool:
        """Check if a state transition is valid."""
        valid = self._transitions.get(current, [])
        return target in valid

    def get_valid_transitions(self, state: AgentState) -> list[AgentState]:
        """Get list of valid target states from the given state."""
        return list(self._transitions.get(state, []))
