"""Dynamic replanning for Brain OS.

When execution fails, modifies the plan to attempt recovery by removing
failed steps, substituting models/providers, or simplifying the plan.
"""

import uuid

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType

logger = structlog.get_logger()

# Fallback model options
FALLBACK_MODELS: list[tuple[str, str]] = [
    ("gpt-4o-mini", "openai"),
    ("claude-3-haiku", "anthropic"),
    ("llama3.2", "ollama"),
]


class DynamicReplanner:
    """Modifies execution plans when execution fails.

    Provides strategies for plan recovery including removing failed steps,
    substituting models/providers, and simplifying complex plans.
    """

    def __init__(
        self,
        fallback_models: list[tuple[str, str]] | None = None,
    ) -> None:
        """Initialize replanner with fallback model options.

        Args:
            fallback_models: List of (model_id, provider) tuples to try.
        """
        self._fallback_models = fallback_models or FALLBACK_MODELS

    def replan(
        self,
        plan: ExecutionPlan,
        results: list[StepResult],
    ) -> ExecutionPlan | None:
        """Create a modified plan based on execution failures.

        Attempts recovery strategies in order:
        1. Remove non-critical failed steps
        2. Substitute model/provider for LLM failures
        3. Simplify plan by removing optional steps

        Args:
            plan: The original plan that failed.
            results: Step results from the failed execution.

        Returns:
            A new ExecutionPlan if replanning is possible, None otherwise.
        """
        failed_step_ids = {r.step_id for r in results if r.state == StepState.FAILED}

        if not failed_step_ids:
            return None

        logger.info(
            "replanning_started",
            plan_id=plan.plan_id,
            failed_steps=list(failed_step_ids),
        )

        # Strategy 1: Try to remove failed non-LLM steps
        new_plan = self._remove_failed_steps(plan, failed_step_ids)
        if new_plan and self._has_llm_step(new_plan):
            logger.info("replanning_removed_steps", new_plan_id=new_plan.plan_id)
            return new_plan

        # Strategy 2: Substitute model/provider
        new_plan = self._substitute_model(plan, failed_step_ids)
        if new_plan:
            logger.info("replanning_substituted_model", new_plan_id=new_plan.plan_id)
            return new_plan

        # Strategy 3: Simplify plan (remove tool calls, keep LLM only)
        new_plan = self._simplify_plan(plan)
        if new_plan:
            logger.info("replanning_simplified", new_plan_id=new_plan.plan_id)
            return new_plan

        logger.warning("replanning_failed", plan_id=plan.plan_id)
        return None

    def _remove_failed_steps(
        self,
        plan: ExecutionPlan,
        failed_step_ids: set[str],
    ) -> ExecutionPlan | None:
        """Remove failed steps if they are not critical (non-LLM).

        Args:
            plan: Original plan.
            failed_step_ids: IDs of steps that failed.

        Returns:
            New plan without failed steps, or None if removal not possible.
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}

        # Only remove non-LLM failed steps
        removable = {
            sid
            for sid in failed_step_ids
            if step_types.get(sid) != ExecutionStepType.LLM_CALL
        }

        if not removable:
            return None

        # Remove steps and update dependencies
        new_steps: list[ExecutionStep] = []
        for step in plan.steps:
            if step.step_id in removable:
                continue
            # Remove references to removed steps in depends_on
            new_depends = [d for d in step.depends_on if d not in removable]
            new_step = ExecutionStep(
                step_id=step.step_id,
                step_type=step.step_type,
                target=step.target,
                params=step.params,
                depends_on=new_depends,
                timeout_seconds=step.timeout_seconds,
                retryable=step.retryable,
                priority=step.priority,
            )
            new_steps.append(new_step)

        if not new_steps:
            return None

        return ExecutionPlan(
            plan_id=f"replan-{uuid.uuid4().hex[:8]}",
            intent=plan.intent,
            steps=new_steps,
            model_id=plan.model_id,
            provider=plan.provider,
            context=plan.context,
            confidence=plan.confidence,
            estimated_latency_ms=plan.estimated_latency_ms,
            requires_streaming=plan.requires_streaming,
            fallback_plan_id=plan.plan_id,
        )

    def _substitute_model(
        self,
        plan: ExecutionPlan,
        failed_step_ids: set[str],
    ) -> ExecutionPlan | None:
        """Substitute the model/provider for failed LLM steps.

        Args:
            plan: Original plan.
            failed_step_ids: IDs of steps that failed.

        Returns:
            New plan with substituted model, or None if no fallback available.
        """
        # Find a fallback model different from the current one
        current = (plan.model_id, plan.provider)
        fallback = None
        for model_id, provider in self._fallback_models:
            if (model_id, provider) != current:
                fallback = (model_id, provider)
                break

        if fallback is None:
            return None

        new_model_id, new_provider = fallback

        # Update LLM steps with new model
        new_steps: list[ExecutionStep] = []
        for step in plan.steps:
            if step.step_id in failed_step_ids and step.step_type == ExecutionStepType.LLM_CALL:
                new_step = ExecutionStep(
                    step_id=step.step_id,
                    step_type=step.step_type,
                    target=new_model_id,
                    params=step.params,
                    depends_on=step.depends_on,
                    timeout_seconds=step.timeout_seconds,
                    retryable=step.retryable,
                    priority=step.priority,
                )
                new_steps.append(new_step)
            else:
                new_steps.append(step)

        return ExecutionPlan(
            plan_id=f"replan-{uuid.uuid4().hex[:8]}",
            intent=plan.intent,
            steps=new_steps,
            model_id=new_model_id,
            provider=new_provider,
            context=plan.context,
            confidence=plan.confidence,
            estimated_latency_ms=plan.estimated_latency_ms,
            requires_streaming=plan.requires_streaming,
            fallback_plan_id=plan.plan_id,
        )

    def _simplify_plan(self, plan: ExecutionPlan) -> ExecutionPlan | None:
        """Simplify plan by keeping only LLM steps.

        Removes tool calls, agent delegations, and other non-essential steps
        to create a minimal LLM-only plan.

        Args:
            plan: Original plan.

        Returns:
            Simplified plan or None if no LLM steps exist.
        """
        llm_steps = [
            ExecutionStep(
                step_id=s.step_id,
                step_type=s.step_type,
                target=s.target,
                params=s.params,
                depends_on=[],  # Remove all deps for simplification
                timeout_seconds=s.timeout_seconds,
                retryable=s.retryable,
                priority=s.priority,
            )
            for s in plan.steps
            if s.step_type == ExecutionStepType.LLM_CALL
        ]

        if not llm_steps:
            return None

        return ExecutionPlan(
            plan_id=f"replan-{uuid.uuid4().hex[:8]}",
            intent=plan.intent,
            steps=llm_steps,
            model_id=plan.model_id,
            provider=plan.provider,
            context=plan.context,
            confidence=plan.confidence,
            estimated_latency_ms=plan.estimated_latency_ms,
            requires_streaming=plan.requires_streaming,
            fallback_plan_id=plan.plan_id,
        )

    def _has_llm_step(self, plan: ExecutionPlan) -> bool:
        """Check if plan has at least one LLM step.

        Args:
            plan: Plan to check.

        Returns:
            True if plan contains an LLM_CALL step.
        """
        return any(s.step_type == ExecutionStepType.LLM_CALL for s in plan.steps)
