"""Maps agent capabilities to system agent types."""

from __future__ import annotations

from agents.schemas import Agent, AgentType
from config.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_MAPPINGS: dict[str, AgentType] = {
    "planning": AgentType.PLANNER,
    "decomposition": AgentType.PLANNER,
    "search": AgentType.RESEARCH,
    "analysis": AgentType.RESEARCH,
    "storage": AgentType.MEMORY,
    "retrieval": AgentType.MEMORY,
    "inference": AgentType.REASONING,
    "logic": AgentType.REASONING,
    "validation": AgentType.VERIFICATION,
    "code_generation": AgentType.CODING,
    "debugging": AgentType.CODING,
    "test_generation": AgentType.TESTING,
    "test_execution": AgentType.TESTING,
    "threat_analysis": AgentType.SECURITY,
    "vulnerability_scan": AgentType.SECURITY,
    "deployment": AgentType.DEVOPS,
    "monitoring": AgentType.MONITORING,
    "doc_generation": AgentType.DOCUMENTATION,
    "summarization": AgentType.DOCUMENTATION,
    "task_execution": AgentType.EXECUTION,
    "orchestration": AgentType.EXECUTION,
    "metrics": AgentType.MONITORING,
    "alerting": AgentType.MONITORING,
    "pattern_recognition": AgentType.LEARNING,
    "adaptation": AgentType.LEARNING,
    "messaging": AgentType.COMMUNICATION,
    "notification": AgentType.COMMUNICATION,
    "fault_recovery": AgentType.RECOVERY,
    "rollback": AgentType.RECOVERY,
}


class AgentCapabilityMapper:
    """Maps capabilities to agent types and vice versa."""

    def __init__(self) -> None:
        self._mappings: dict[str, AgentType] = dict(_DEFAULT_MAPPINGS)

    def map_to_agent_type(self, capability: str) -> AgentType | None:
        """Map a capability string to an agent type."""
        return self._mappings.get(capability)

    def map_from_agent(self, agent: Agent) -> list[str]:
        """Get all known capability strings for an agent."""
        return [cap for cap, atype in self._mappings.items() if atype == agent.agent_type]

    def register_mapping(self, capability: str, agent_type: AgentType) -> None:
        """Register a new capability-to-type mapping."""
        self._mappings[capability] = agent_type
        logger.debug("capability_mapped", capability=capability, agent_type=agent_type.value)
