"""Research Agent - specialized in web search, summarization, and fact-checking."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """Agent specialized in research, web search, and summarization."""

    def __init__(self, agent_id: str = "research-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Research Agent",
            agent_type=AgentType.RESEARCH,
            role=AgentRole.SPECIALIST,
            capabilities=[
                AgentCapability.RESEARCH,
                AgentCapability.SUMMARIZATION,
                AgentCapability.DATA_ANALYSIS,
            ],
            max_concurrent_tasks=5,
            priority=4,
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute research task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}

        # Simulated research processing
        sources_count = len(context.get("sources", [])) or 3
        output_parts = [
            f"Agent [Research Agent] processed: {instruction}",
            f"Sources analyzed: {sources_count}",
            "Key findings synthesized and summarized.",
        ]

        if "summarize" in instruction.lower():
            output_parts.append("Summary generated from source materials.")
        elif "analyze" in instruction.lower():
            output_parts.append("Data analysis complete with insights extracted.")
        else:
            output_parts.append("Research completed with relevant findings.")

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.RESEARCH,
            output="\n".join(output_parts),
            status="success",
            tokens_used=450,
        )
