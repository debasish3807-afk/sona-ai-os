"""Execution Agent - specialized in task execution and automation."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class ExecutionAgent(BaseAgent):
    """Agent specialized in task execution, automation, and workflow running."""

    def __init__(self, agent_id: str = "execution-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Execution Agent",
            agent_type=AgentType.AUTOMATION,
            role=AgentRole.WORKER,
            capabilities=[
                AgentCapability.TASK_EXECUTION,
                AgentCapability.DATA_ANALYSIS,
            ],
            max_concurrent_tasks=4,
            priority=3,
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute automation task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}
        workflow = context.get("workflow", "default")

        output_parts = [
            f"Agent [Execution Agent] processed: {instruction}",
            f"Workflow: {workflow}",
        ]

        if "run" in instruction.lower() or "execute" in instruction.lower():
            output_parts.append("Workflow executed successfully.")
            output_parts.append("All steps completed without errors.")
        elif "schedule" in instruction.lower():
            output_parts.append("Task scheduled for execution.")
            output_parts.append("Notification will be sent on completion.")
        elif "automate" in instruction.lower():
            output_parts.append("Automation pipeline configured.")
            output_parts.append("Triggers set and workflow active.")
        else:
            output_parts.append("Task execution completed.")
            output_parts.append("Results stored and ready for review.")

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.AUTOMATION,
            output="\n".join(output_parts),
            status="success",
            tokens_used=200,
        )
