"""Manager Agent - specialized in delegation and coordination."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class ManagerAgent(BaseAgent):
    """Agent specialized in delegation, coordination, and task management.

    The manager agent oversees other agents and handles complex tasks
    by delegating subtasks to appropriate specialists.
    """

    def __init__(self, agent_id: str = "manager-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Manager Agent",
            agent_type=AgentType.PLANNER,
            role=AgentRole.MANAGER,
            capabilities=[
                AgentCapability.DELEGATION,
                AgentCapability.PLANNING,
                AgentCapability.QUALITY_REVIEW,
            ],
            max_concurrent_tasks=2,
            priority=1,
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute management task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}

        output_parts = [
            f"Agent [Manager Agent] processed: {instruction}",
        ]

        if "delegate" in instruction.lower():
            target = context.get("delegate_to", "available worker")
            output_parts.append(f"Task delegated to: {target}")
            output_parts.append("Delegation chain established.")
            output_parts.append("Monitoring subtask progress.")
        elif "coordinate" in instruction.lower():
            team_size = context.get("team_size", 3)
            output_parts.append(f"Coordinating team of {team_size} agents.")
            output_parts.append("Work distribution optimized.")
        elif "plan" in instruction.lower():
            output_parts.append("Strategic plan created.")
            output_parts.append("Tasks decomposed and assigned.")
        else:
            output_parts.append("Management action completed.")
            output_parts.append("Team status reviewed and tasks prioritized.")

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.PLANNER,
            output="\n".join(output_parts),
            status="success",
            tokens_used=250,
        )
