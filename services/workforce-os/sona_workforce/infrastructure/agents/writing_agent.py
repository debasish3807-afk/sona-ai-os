"""Writing Agent - specialized in content writing and documentation."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class WritingAgent(BaseAgent):
    """Agent specialized in writing, documentation, and content creation."""

    def __init__(self, agent_id: str = "writing-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Writing Agent",
            agent_type=AgentType.COMMUNICATION,
            role=AgentRole.SPECIALIST,
            capabilities=[
                AgentCapability.WRITING,
                AgentCapability.SUMMARIZATION,
            ],
            max_concurrent_tasks=4,
            priority=5,
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute writing task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}
        tone = context.get("tone", "professional")

        output_parts = [
            f"Agent [Writing Agent] processed: {instruction}",
            f"Tone: {tone}",
        ]

        if "document" in instruction.lower() or "doc" in instruction.lower():
            output_parts.append("Documentation generated with clear structure.")
            output_parts.append("Includes: overview, usage examples, and API reference.")
        elif "email" in instruction.lower() or "message" in instruction.lower():
            output_parts.append("Communication drafted with appropriate tone.")
        elif "summarize" in instruction.lower():
            output_parts.append("Content summarized to key points.")
        else:
            output_parts.append("Content written with clarity and precision.")
            output_parts.append("Proofread and formatted for readability.")

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.COMMUNICATION,
            output="\n".join(output_parts),
            status="success",
            tokens_used=500,
        )
