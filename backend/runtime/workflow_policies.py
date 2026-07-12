"""Workflow execution policies and policy engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config.logging import get_logger
from runtime.schemas import Workflow, WorkflowTask

logger = get_logger(__name__)


@dataclass
class WorkflowPolicies:
    """Configuration policies for workflow execution."""

    max_retries: int = 3
    task_timeout_seconds: float = 60.0
    workflow_timeout_seconds: float = 600.0
    max_parallel_tasks: int = 4
    checkpoint_interval: int = 3
    failure_threshold: float = 0.5
    priority_boost_on_retry: bool = True


class PolicyEngine:
    """Evaluates and enforces workflow policies."""

    def __init__(self) -> None:
        self._evaluations: list[dict[str, Any]] = []

    def evaluate(self, workflow: Workflow, policies: WorkflowPolicies) -> dict[str, Any]:
        """Evaluate a workflow against policies and return violations/warnings."""
        violations: list[str] = []
        warnings: list[str] = []

        if len(workflow.tasks) > policies.max_parallel_tasks * 10:
            warnings.append(
                f"Workflow has {len(workflow.tasks)} tasks, "
                f"exceeds recommended max ({policies.max_parallel_tasks * 10})"
            )

        for task in workflow.tasks:
            if task.timeout_seconds > policies.workflow_timeout_seconds:
                violations.append(
                    f"Task '{task.name}' timeout ({task.timeout_seconds}s) "
                    f"exceeds workflow timeout ({policies.workflow_timeout_seconds}s)"
                )
            if task.max_retries > policies.max_retries:
                warnings.append(
                    f"Task '{task.name}' max_retries ({task.max_retries}) "
                    f"exceeds policy max ({policies.max_retries})"
                )

        failed_count = sum(1 for t in workflow.tasks if t.result.get("error"))
        if workflow.tasks and (failed_count / len(workflow.tasks)) > policies.failure_threshold:
            violations.append(
                f"Failure rate ({failed_count}/{len(workflow.tasks)}) "
                f"exceeds threshold ({policies.failure_threshold})"
            )

        result: dict[str, Any] = {
            "violations": violations,
            "warnings": warnings,
            "compliant": len(violations) == 0,
        }
        self._evaluations.append(result)
        return result

    def apply_retry_policy(self, task: WorkflowTask, policies: WorkflowPolicies) -> bool:
        """Apply retry policy to a task. Returns True if retry is allowed."""
        if task.retry_count >= policies.max_retries:
            return False
        if policies.priority_boost_on_retry and task.retry_count > 0:
            current = int(task.priority)
            if current > 0:
                from runtime.schemas import QueuePriority

                task.priority = QueuePriority(current - 1)
        return True

    def apply_timeout_policy(self, task: WorkflowTask, policies: WorkflowPolicies) -> bool:
        """Apply timeout policy. Returns True if task duration exceeds timeout."""
        return task.duration_ms > (policies.task_timeout_seconds * 1000)
