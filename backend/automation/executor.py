"""Workflow executor — runs workflow steps with control flow."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from automation.actions import execute_action
from automation.schemas import (
    ActionStep,
    StepType,
    Workflow,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
)
from config.logging import get_logger

logger = get_logger(__name__)


class WorkflowExecutor:
    """Executes workflow steps with IF/ELSE/LOOP/PARALLEL/WAIT."""

    async def run(self, workflow: Workflow) -> WorkflowRun:
        """Execute a complete workflow."""
        run = WorkflowRun(
            run_id=str(uuid.uuid4()),
            workflow_id=workflow.workflow_id,
            status=WorkflowStatus.RUNNING,
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            steps_total=len(workflow.steps),
        )
        context: dict[str, Any] = {"workflow_id": workflow.workflow_id}

        try:
            for step in workflow.steps:
                result = await self._execute_step(step, context)
                context["last_result"] = result
                run.steps_completed += 1

            run.status = WorkflowStatus.COMPLETED
            run.output = context.get("last_result", {})
        except Exception as exc:
            run.status = WorkflowStatus.FAILED
            run.error = str(exc)
            logger.error("workflow_failed", workflow_id=workflow.workflow_id, error=str(exc))

        run.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        return run

    async def _execute_step(self, step: WorkflowStep, ctx: dict[str, Any]) -> dict[str, Any]:
        """Execute a single workflow step."""
        if step.step_type == StepType.ACTION and step.action:
            return await self._run_action(step.action, ctx)

        if step.step_type == StepType.CONDITION:
            return await self._run_condition(step, ctx)

        if step.step_type == StepType.LOOP and step.steps:
            return await self._run_loop(step, ctx)

        if step.step_type == StepType.PARALLEL and step.steps:
            return await self._run_parallel(step, ctx)

        if step.step_type == StepType.WAIT:
            await asyncio.sleep(min(step.wait_seconds, 60.0))
            return {"waited": step.wait_seconds}

        return {}

    async def _run_action(self, action: ActionStep, ctx: dict[str, Any]) -> dict[str, Any]:
        """Execute action with optional retry."""
        last_error = ""
        for attempt in range(action.retry + 1):
            try:
                return await asyncio.wait_for(
                    execute_action(action, ctx),
                    timeout=action.timeout_seconds,
                )
            except TimeoutError:
                last_error = "Action timed out"
            except Exception as exc:
                last_error = str(exc)
            if attempt < action.retry:
                await asyncio.sleep(1.0 * (attempt + 1))
        return {"error": last_error}

    async def _run_condition(self, step: WorkflowStep, ctx: dict[str, Any]) -> dict[str, Any]:
        """Evaluate condition and run true/false branch."""
        cond = step.condition
        if cond is None:
            return {}

        last = ctx.get("last_result", {})
        actual = last.get(cond.field, None)
        met = self._evaluate(actual, cond.operator, cond.value)

        branch = step.on_true if met else step.on_false
        if branch:
            for s in branch:
                result = await self._execute_step(s, ctx)
                ctx["last_result"] = result
            result_val: dict[str, Any] = ctx.get("last_result", {})
        return result_val
        return {"condition_met": met}

    async def _run_loop(self, step: WorkflowStep, ctx: dict[str, Any]) -> dict[str, Any]:
        """Run steps in a loop (max 100 iterations)."""
        results: list[dict[str, Any]] = []
        for _i in range(min(int(step.wait_seconds) or 3, 100)):
            for s in step.steps or []:
                result = await self._execute_step(s, ctx)
                ctx["last_result"] = result
                results.append(result)
        return {"iterations": len(results), "last": results[-1] if results else {}}

    async def _run_parallel(self, step: WorkflowStep, ctx: dict[str, Any]) -> dict[str, Any]:
        """Run steps in parallel."""
        tasks = [self._execute_step(s, ctx) for s in (step.steps or [])]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        outputs: list[dict[str, Any]] = []
        for r in results:
            if isinstance(r, BaseException):
                outputs.append({"error": str(r)})
            else:
                outputs.append(r)
        return {"parallel_results": outputs}

    @staticmethod
    def _evaluate(actual: Any, operator: str, expected: Any) -> bool:
        """Evaluate a condition."""
        if operator == "eq":
            return bool(actual == expected)
        if operator == "ne":
            return bool(actual != expected)
        if operator == "gt":
            return bool(actual is not None and actual > expected)
        if operator == "lt":
            return bool(actual is not None and actual < expected)
        if operator == "contains":
            return bool(expected in str(actual)) if actual else False
        if operator == "exists":
            return actual is not None
        return False
