"""Reviewer Agent - specialized in quality review and feedback."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    """Agent specialized in quality review, feedback, and validation."""

    def __init__(self, agent_id: str = "reviewer-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Reviewer Agent",
            agent_type=AgentType.CODING,
            role=AgentRole.REVIEWER,
            capabilities=[
                AgentCapability.QUALITY_REVIEW,
                AgentCapability.CODE_REVIEW,
                AgentCapability.SUMMARIZATION,
            ],
            max_concurrent_tasks=3,
            priority=2,
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute review task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}
        review_type = context.get("review_type", "general")

        output_parts = [
            f"Agent [Reviewer Agent] processed: {instruction}",
            f"Review type: {review_type}",
        ]

        if "code" in instruction.lower():
            output_parts.append("Code review completed.")
            output_parts.append("Quality score: 8.5/10")
            output_parts.append("Suggestions: 3 improvements identified.")
        elif "quality" in instruction.lower():
            output_parts.append("Quality assessment completed.")
            output_parts.append("Standards compliance: PASS")
        elif "validate" in instruction.lower():
            output_parts.append("Validation checks passed.")
            output_parts.append("All assertions satisfied.")
        else:
            output_parts.append("Review completed with detailed feedback.")
            output_parts.append("Recommendations provided for improvement.")

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.CODING,
            output="\n".join(output_parts),
            status="success",
            tokens_used=350,
        )
