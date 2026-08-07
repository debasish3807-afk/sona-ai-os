"""Planning Agent - specialized in task planning and project structuring."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class PlanningAgent(BaseAgent):
    """Agent specialized in task planning, project structuring, and roadmapping."""

    def __init__(self, agent_id: str = "planning-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Planning Agent",
            agent_type=AgentType.PLANNER,
            role=AgentRole.SPECIALIST,
            capabilities=[
                AgentCapability.PLANNING,
                AgentCapability.TASK_EXECUTION,
            ],
            max_concurrent_tasks=4,
            priority=2,
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute planning task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}
        project_name = context.get("project", "unnamed")

        output_parts = [
            f"Agent [Planning Agent] processed: {instruction}",
            f"Project: {project_name}",
        ]

        if "roadmap" in instruction.lower():
            output_parts.append("Roadmap created with milestones and deliverables.")
            output_parts.append("Timeline: Estimated 4 sprints.")
        elif "breakdown" in instruction.lower() or "split" in instruction.lower():
            output_parts.append("Task breakdown completed.")
            output_parts.append("Subtasks identified with dependencies mapped.")
        else:
            output_parts.append("Plan created with clear objectives and action items.")
            output_parts.append("Dependencies identified and prioritized.")

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.PLANNER,
            output="\n".join(output_parts),
            status="success",
            tokens_used=350,
        )
