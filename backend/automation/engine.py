"""Automation Engine — orchestrates workflows, history, templates."""

from __future__ import annotations

import time
import uuid
from typing import Any

from automation.executor import WorkflowExecutor
from automation.schemas import (
    Trigger,
    Workflow,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
)
from config.logging import get_logger

logger = get_logger(__name__)


class AutomationEngine:
    """Central automation orchestrator."""

    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._history: list[WorkflowRun] = []
        self._executor = WorkflowExecutor()

    def create_workflow(
        self,
        name: str,
        steps: list[WorkflowStep],
        trigger: Trigger | None = None,
        description: str = "",
    ) -> Workflow:
        """Create and register a new workflow."""
        wf = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=description,
            trigger=trigger,
            steps=steps,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self._workflows[wf.workflow_id] = wf
        logger.info("workflow_created", id=wf.workflow_id, name=name)
        return wf

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[Workflow]:
        return list(self._workflows.values())

    def delete_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False

    async def run_workflow(self, workflow_id: str) -> WorkflowRun:
        """Execute a workflow by ID."""
        wf = self._workflows.get(workflow_id)
        if wf is None:
            return WorkflowRun(
                run_id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error="Workflow not found",
            )
        run = await self._executor.run(wf)
        self._history.append(run)
        logger.info("workflow_completed", id=workflow_id, status=run.status.value)
        return run

    def get_history(self, limit: int = 50) -> list[WorkflowRun]:
        return self._history[-limit:]

    def get_templates(self) -> list[dict[str, Any]]:
        """Built-in workflow templates."""
        return [
            {
                "id": "daily_research",
                "name": "Daily Research Summary",
                "description": "Research a topic and store summary in memory",
                "steps": [
                    {"type": "deep_research", "params": {"query": "{{topic}}"}},
                    {"type": "memory_store", "params": {"content": "{{result.summary}}"}},
                    {"type": "notification", "params": {"message": "Research complete"}},
                ],
            },
            {
                "id": "ocr_and_index",
                "name": "OCR & Index Document",
                "description": "OCR an image and store text in knowledge base",
                "steps": [
                    {"type": "ocr", "params": {"image_base64": "{{image}}"}},
                    {"type": "memory_store", "params": {"content": "{{result.text}}"}},
                ],
            },
            {
                "id": "monitor_file",
                "name": "Monitor File Changes",
                "description": "Watch a file and notify on change",
                "steps": [
                    {"type": "file_read", "params": {"path": "{{file_path}}"}},
                    {"type": "notification", "params": {"message": "File changed: {{file_path}}"}},
                ],
            },
            {
                "id": "ai_review",
                "name": "AI Code Review",
                "description": "Read a file and ask AI to review it",
                "steps": [
                    {"type": "file_read", "params": {"path": "{{file_path}}"}},
                    {
                        "type": "ai_chat",
                        "params": {"message": "Review this code: {{result.content}}"},
                    },
                    {"type": "notification", "params": {"message": "Review complete"}},
                ],
            },
        ]

    def get_status(self) -> dict[str, Any]:
        return {
            "workflows": len(self._workflows),
            "runs_total": len(self._history),
            "runs_completed": sum(1 for r in self._history if r.status == WorkflowStatus.COMPLETED),
            "runs_failed": sum(1 for r in self._history if r.status == WorkflowStatus.FAILED),
        }
