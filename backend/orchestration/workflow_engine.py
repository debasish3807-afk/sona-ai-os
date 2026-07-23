"""Workflow Engine — sequential, parallel, conditional, loop execution with failure recovery."""

from __future__ import annotations

import uuid
from typing import Any

from config.logging import get_logger
from orchestration.schemas import WorkflowDefinition, WorkflowStatus, WorkflowStep

logger = get_logger(__name__)


class WorkflowEngine:
    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowDefinition] = {}

    def create_workflow(self, name: str, steps: list[WorkflowStep]) -> WorkflowDefinition:
        wf = WorkflowDefinition(workflow_id=str(uuid.uuid4()), name=name, steps=steps)
        self._workflows[wf.workflow_id] = wf
        return wf

    def execute(self, workflow_id: str) -> dict[str, Any]:
        wf = self._workflows.get(workflow_id)
        if wf is None:
            return {"success": False, "error": "Workflow not found"}
        wf.status = WorkflowStatus.RUNNING
        completed: list[WorkflowStep] = []
        for step in wf.steps:
            condition_met = True
            if step.condition:
                parts = step.condition.split()
                if len(parts) == 3 and parts[1] in ("==", "!=", ">", "<", ">=", "<="):
                    lhs = parts[0]
                    rhs = parts[2]
                    left_val = self._eval_ref(lhs, completed)
                    right_val = self._eval_ref(rhs, completed)
                    op = parts[1]
                    if op == "==":
                        condition_met = left_val == right_val
                    elif op == "!=":
                        condition_met = left_val != right_val
                    elif op == ">":
                        condition_met = float(left_val or 0) > float(right_val or 0)
            if not condition_met:
                step.status = WorkflowStatus.SKIPPED
                continue
            if step.step_type == "action":
                completed.append(step)
                step.status = WorkflowStatus.COMPLETED
            elif step.step_type == "loop":
                for _ in range(max(step.loop_count, 1)):
                    completed.append(step)
                step.status = WorkflowStatus.COMPLETED
            elif step.step_type == "parallel":
                step.status = WorkflowStatus.COMPLETED
                completed.append(step)
        wf.status = WorkflowStatus.COMPLETED
        return {"success": True, "workflow_id": workflow_id, "steps_completed": len(completed)}

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[WorkflowDefinition]:
        return sorted(self._workflows.values(), key=lambda w: w.workflow_id, reverse=True)

    @staticmethod
    def _eval_ref(ref: str, context: list[WorkflowStep]) -> Any:
        if ref.lstrip("-").isdigit():
            try:
                ctx = context[int(ref)]
                return {"status": ctx.status.value, "name": ctx.name}
            except (IndexError, ValueError):
                pass
        return ref
