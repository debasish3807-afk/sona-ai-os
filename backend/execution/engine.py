"""Execution Engine — executes plans step by step with resilience.

Handles:
    - Sequential execution with dependency resolution
    - Retry with backoff on transient failures
    - Conditional step skipping
    - Timeout enforcement per step and overall
    - Result aggregation and reporting
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger
from mcp.server import get_mcp_server
from planner.plan import ExecutionPlan, PlanStatus, PlanStep, StepStatus

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """Final result of executing a plan."""

    plan_id: str
    status: str  # PlanStatus value
    steps_completed: int
    steps_failed: int
    steps_total: int
    total_duration_ms: float
    outputs: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""


class ExecutionEngine:
    """Executes tool plans with retry, timeout, and safety controls.

    Processes each step sequentially (respecting dependencies),
    retries failed steps, and produces a consolidated result.
    """

    def __init__(
        self,
        max_step_timeout: int = 60,
        max_plan_timeout: int = 300,
        max_retries: int = 1,
    ) -> None:
        self._max_step_timeout = max_step_timeout
        self._max_plan_timeout = max_plan_timeout
        self._max_retries = max_retries

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        session_id: str | None = None,
    ) -> ExecutionResult:
        """Execute all steps in a plan sequentially.

        Args:
            plan: The execution plan to run.
            session_id: Optional session for MCP tracking.

        Returns:
            ExecutionResult with aggregated outcomes.
        """
        plan.status = PlanStatus.EXECUTING
        plan_start = time.perf_counter()
        mcp = get_mcp_server()
        outputs: list[dict[str, Any]] = []

        logger.info(
            "Executing plan",
            plan_id=plan.plan_id,
            steps=plan.step_count,
        )

        while True:
            # Check overall timeout
            elapsed = (time.perf_counter() - plan_start) * 1000
            if elapsed > self._max_plan_timeout * 1000:
                logger.warning("Plan execution timed out", plan_id=plan.plan_id)
                self._timeout_remaining(plan)
                break

            step = plan.get_next_step()
            if step is None:
                break  # All steps processed or blocked

            # Execute step
            step_result = await self._execute_step(step, mcp, session_id, outputs)
            outputs.append(step_result)

        # Finalize
        plan.total_duration_ms = (time.perf_counter() - plan_start) * 1000
        plan.finalize()

        summary = self._build_summary(plan, outputs)
        logger.info(
            "Plan execution complete",
            plan_id=plan.plan_id,
            status=plan.status.value,
            duration_ms=round(plan.total_duration_ms, 2),
        )

        return ExecutionResult(
            plan_id=plan.plan_id,
            status=plan.status.value,
            steps_completed=plan.completed_count,
            steps_failed=plan.failed_count,
            steps_total=plan.step_count,
            total_duration_ms=plan.total_duration_ms,
            outputs=outputs,
            summary=summary,
        )

    async def _execute_step(
        self,
        step: PlanStep,
        mcp: Any,
        session_id: str | None,
        previous_outputs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute a single step with retry logic."""
        step.mark_running()
        step_start = time.perf_counter()

        # Resolve dynamic params from previous step outputs
        resolved_params = self._resolve_params(step, previous_outputs)

        for attempt in range(self._max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    mcp.execute_tool(step.tool_name, resolved_params, session_id),
                    timeout=self._max_step_timeout,
                )
                duration_ms = (time.perf_counter() - step_start) * 1000

                if result.success:
                    step.mark_completed(result.output, duration_ms)
                    return {
                        "step_id": step.step_id,
                        "tool": step.tool_name,
                        "success": True,
                        "output": result.output[:2000],
                        "duration_ms": round(duration_ms, 2),
                    }

                # Tool returned failure
                if attempt < self._max_retries:
                    step.retry_count += 1
                    step.status = StepStatus.RETRYING
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue

                step.mark_failed(result.error or "Tool execution failed", duration_ms)
                return {
                    "step_id": step.step_id,
                    "tool": step.tool_name,
                    "success": False,
                    "error": result.error,
                    "duration_ms": round(duration_ms, 2),
                }

            except TimeoutError:
                duration_ms = (time.perf_counter() - step_start) * 1000
                step.mark_failed(f"Step timed out after {self._max_step_timeout}s", duration_ms)
                return {
                    "step_id": step.step_id,
                    "tool": step.tool_name,
                    "success": False,
                    "error": f"Timeout after {self._max_step_timeout}s",
                    "duration_ms": round(duration_ms, 2),
                }

            except Exception as exc:
                duration_ms = (time.perf_counter() - step_start) * 1000
                step.mark_failed(str(exc), duration_ms)
                return {
                    "step_id": step.step_id,
                    "tool": step.tool_name,
                    "success": False,
                    "error": str(exc),
                    "duration_ms": round(duration_ms, 2),
                }

        # Should not reach here, but safety return
        duration_ms = (time.perf_counter() - step_start) * 1000
        step.mark_failed("Max retries exceeded", duration_ms)
        return {
            "step_id": step.step_id,
            "tool": step.tool_name,
            "success": False,
            "error": "Max retries exceeded",
            "duration_ms": round(duration_ms, 2),
        }

    def _resolve_params(
        self,
        step: PlanStep,
        previous_outputs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Resolve step parameters, injecting outputs from previous steps."""
        params = dict(step.params)
        # If params reference previous outputs, inject them
        if previous_outputs and not params.get("path") and not params.get("command"):
            # Use the last successful output as context if relevant
            last_success = next(
                (o for o in reversed(previous_outputs) if o.get("success")),
                None,
            )
            if last_success and "output" in last_success:
                params.setdefault("_previous_output", last_success["output"][:500])
        return params

    def _timeout_remaining(self, plan: ExecutionPlan) -> None:
        """Mark all remaining pending steps as failed due to timeout."""
        for step in plan.steps:
            if step.status == StepStatus.PENDING:
                step.mark_failed("Plan timeout exceeded", 0.0)

    def _build_summary(self, plan: ExecutionPlan, outputs: list[dict[str, Any]]) -> str:
        """Build a human-readable summary of execution."""
        lines: list[str] = [
            f"Plan: {plan.description}",
            f"Status: {plan.status.value}",
            f"Steps: {plan.completed_count}/{plan.step_count} completed",
            f"Duration: {plan.total_duration_ms:.0f}ms",
            "",
        ]
        for out in outputs:
            status_icon = "✓" if out.get("success") else "✗"
            tool = out.get("tool", "?")
            duration = out.get("duration_ms", 0)
            lines.append(f"  {status_icon} {tool} ({duration:.0f}ms)")
            if out.get("error"):
                lines.append(f"    Error: {out['error'][:100]}")
        return "\n".join(lines)
