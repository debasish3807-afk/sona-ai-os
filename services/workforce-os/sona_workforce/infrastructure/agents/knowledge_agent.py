"""Knowledge Agent - specialized in knowledge retrieval and organization."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class KnowledgeAgent(BaseAgent):
    """Agent specialized in knowledge retrieval, organization, and indexing."""

    def __init__(self, agent_id: str = "knowledge-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Knowledge Agent",
            agent_type=AgentType.RESEARCH,
            role=AgentRole.SPECIALIST,
            capabilities=[
                AgentCapability.KNOWLEDGE_RETRIEVAL,
                AgentCapability.RESEARCH,
                AgentCapability.SUMMARIZATION,
            ],
            max_concurrent_tasks=5,
            priority=4,
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute knowledge retrieval task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}
        domain = context.get("domain", "general")

        output_parts = [
            f"Agent [Knowledge Agent] processed: {instruction}",
            f"Knowledge domain: {domain}",
        ]

        if "search" in instruction.lower() or "find" in instruction.lower():
            output_parts.append("Knowledge search completed.")
            output_parts.append("Found 5 relevant knowledge entries.")
        elif "index" in instruction.lower() or "organize" in instruction.lower():
            output_parts.append("Knowledge indexed and organized.")
            output_parts.append("Categories updated with new entries.")
        elif "extract" in instruction.lower():
            output_parts.append("Key knowledge extracted from source.")
            output_parts.append("Structured data available for consumption.")
        else:
            output_parts.append("Knowledge retrieval completed successfully.")
            output_parts.append("Results ranked by relevance.")

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.RESEARCH,
            output="\n".join(output_parts),
            status="success",
            tokens_used=300,
        )
