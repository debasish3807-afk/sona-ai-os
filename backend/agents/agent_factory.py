"""Dynamic agent creation factory."""

from __future__ import annotations

from typing import Any

from agents.schemas import Agent, AgentPriority, AgentType
from config.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_CAPABILITIES: dict[AgentType, list[str]] = {
    AgentType.PLANNER: ["planning", "decomposition"],
    AgentType.RESEARCH: ["search", "analysis"],
    AgentType.MEMORY: ["storage", "retrieval"],
    AgentType.REASONING: ["inference", "logic"],
    AgentType.VERIFICATION: ["validation", "testing"],
    AgentType.CODING: ["code_generation", "debugging"],
    AgentType.TESTING: ["test_generation", "test_execution"],
    AgentType.SECURITY: ["threat_analysis", "vulnerability_scan"],
    AgentType.DEVOPS: ["deployment", "monitoring"],
    AgentType.DOCUMENTATION: ["doc_generation", "summarization"],
    AgentType.EXECUTION: ["task_execution", "orchestration"],
    AgentType.MONITORING: ["metrics", "alerting"],
    AgentType.LEARNING: ["pattern_recognition", "adaptation"],
    AgentType.COMMUNICATION: ["messaging", "notification"],
    AgentType.RECOVERY: ["fault_recovery", "rollback"],
    AgentType.CUSTOM: ["custom"],
}


class AgentFactory:
    """Factory for creating agent instances."""

    def __init__(self) -> None:
        self._created_count: int = 0

    def create(
        self,
        name: str,
        agent_type: AgentType,
        capabilities: list[str] | None = None,
        priority: AgentPriority = AgentPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ) -> Agent:
        """Create a new agent instance."""
        caps = (
            capabilities
            if capabilities is not None
            else self._configure_default_capabilities(agent_type)
        )
        agent = Agent(
            name=name,
            agent_type=agent_type,
            capabilities=caps,
            priority=priority,
            metadata=metadata or {},
        )
        self._created_count += 1
        logger.info("agent_created", agent_id=agent.agent_id, name=name, type=agent_type.value)
        return agent

    def create_team(self, specs: list[dict[str, Any]]) -> list[Agent]:
        """Create a team of agents from specification dicts."""
        agents: list[Agent] = []
        for spec in specs:
            agent = self.create(
                name=spec["name"],
                agent_type=spec["agent_type"],
                capabilities=spec.get("capabilities"),
                priority=spec.get("priority", AgentPriority.NORMAL),
                metadata=spec.get("metadata"),
            )
            agents.append(agent)
        return agents

    def _configure_default_capabilities(self, agent_type: AgentType) -> list[str]:
        """Get default capabilities for an agent type."""
        return list(_DEFAULT_CAPABILITIES.get(agent_type, ["custom"]))
