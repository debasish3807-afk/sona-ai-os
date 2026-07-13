"""Bridge from agent system to the Runtime Engine."""

from __future__ import annotations

from typing import Any

from agents.schemas import AgentTask
from config.logging import get_logger
from runtime.runtime_engine import RuntimeEngine
from runtime.schemas import Workflow, WorkflowTask, WorkflowType

logger = get_logger(__name__)


class AgentRuntimeBridge:
    """Bridges agent tasks to the runtime workflow engine."""

    def __init__(self) -> None:
        self._engine = RuntimeEngine()

    async def submit_to_runtime(self, agent_task: AgentTask) -> str:
        """Submit an agent task as a runtime workflow. Returns workflow_id."""
        wf_task = WorkflowTask(
            name=agent_task.description,
            capability_id=agent_task.agent_id,
            params=agent_task.params,
        )
        workflow = Workflow(
            name=f"agent_task_{agent_task.task_id}",
            workflow_type=WorkflowType.SEQUENTIAL,
            tasks=[wf_task],
        )
        workflow_id = await self._engine.submit_workflow(workflow)
        logger.info(
            "agent_task_submitted_to_runtime", task_id=agent_task.task_id, workflow_id=workflow_id
        )
        return workflow_id

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Get the status of a runtime workflow."""
        workflow = self._engine.get_workflow(workflow_id)
        if workflow is None:
            return {"workflow_id": workflow_id, "state": "not_found"}
        return {"workflow_id": workflow_id, "state": workflow.state.value}

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a runtime workflow."""
        return await self._engine.cancel(workflow_id)
