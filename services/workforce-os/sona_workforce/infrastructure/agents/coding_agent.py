"""Coding Agent - specialized in code generation, review, and debugging."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class CodingAgent(BaseAgent):
    """Agent specialized in code generation, code review, and debugging."""

    def __init__(self, agent_id: str = "coding-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Coding Agent",
            agent_type=AgentType.CODING,
            role=AgentRole.SPECIALIST,
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_REVIEW,
            ],
            max_concurrent_tasks=3,
            priority=3,
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute coding task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}
        language = context.get("language", "python")

        output_parts = [
            f"Agent [Coding Agent] processed: {instruction}",
            f"Language: {language}",
        ]

        if "review" in instruction.lower():
            output_parts.append("Code review completed. No critical issues found.")
            output_parts.append("Suggestions: Consider adding type hints and docstrings.")
        elif "debug" in instruction.lower():
            output_parts.append("Debugging session completed.")
            output_parts.append("Root cause identified and fix applied.")
        elif "test" in instruction.lower():
            output_parts.append("Test cases generated covering edge cases.")
        else:
            output_parts.append("Code generated following best practices.")
            output_parts.append("Implementation includes error handling and documentation.")

        artifacts = [{"type": "code", "language": language}]

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.CODING,
            output="\n".join(output_parts),
            status="success",
            tokens_used=600,
            artifacts=artifacts,
        )
