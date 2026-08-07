"""Brain OS Runtime — the main orchestrator implementation.

Implements BrainOrchestratorPort by accepting a BrainRequest, executing
the associated plan through the scheduler, handling reflection loops,
dynamic replanning on failure, and returning a BrainResponse.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import structlog
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType

from sona_brain.application.ports import BrainOrchestratorPort
from sona_brain.domain.events import (
    ExecutionCompletedEvent,
    ExecutionFailedEvent,
    ExecutionStartedEvent,
)
from sona_brain.domain.execution import ExecutionState, StepState
from sona_brain.domain.models import BrainRequest, BrainResponse
from sona_brain.infrastructure.dynamic_replanner import DynamicReplanner
from sona_brain.infrastructure.execution_scheduler import ExecutionScheduler
from sona_brain.infrastructure.failure_recovery import FailureRecovery, RecoveryAction
from sona_brain.infrastructure.metrics import ExecutionMetrics
from sona_brain.infrastructure.reflection_engine import ReflectionDecision, ReflectionEngine
from sona_brain.infrastructure.result_aggregator import ResultAggregator
from sona_brain.infrastructure.state_manager import ExecutionStateManager
from sona_brain.infrastructure.timeout_recovery import TimeoutRecovery

logger = structlog.get_logger()


class BrainRuntime(BrainOrchestratorPort):
    """Main Brain OS runtime implementation.

    Orchestrates the full execution lifecycle:
    1. Accept a BrainRequest
    2. Build or receive an ExecutionPlan
    3. Execute via the scheduler
    4. Reflect on quality
    5. Replan on failure
    6. Return BrainResponse
    """

    def __init__(
        self,
        scheduler: ExecutionScheduler,
        reflection_engine: ReflectionEngine,
        replanner: DynamicReplanner,
        result_aggregator: ResultAggregator,
        failure_recovery: FailureRecovery,
        timeout_recovery: TimeoutRecovery,
        metrics: ExecutionMetrics,
        default_model: str = "llama3.2",
        default_provider: str = "ollama",
    ) -> None:
        """Initialize the Brain OS runtime.

        Args:
            scheduler: Execution scheduler for plan execution.
            reflection_engine: Quality assessment engine.
            replanner: Dynamic replanning on failure.
            result_aggregator: Combines results into response.
            failure_recovery: Failure classification and recovery.
            timeout_recovery: Timeout handling.
            metrics: Execution metrics tracker.
            default_model: Default model for plan generation.
            default_provider: Default provider for plan generation.
        """
        self._scheduler = scheduler
        self._reflection_engine = reflection_engine
        self._replanner = replanner
        self._result_aggregator = result_aggregator
        self._failure_recovery = failure_recovery
        self._timeout_recovery = timeout_recovery
        self._metrics = metrics
        self._default_model = default_model
        self._default_provider = default_provider
        self._sessions: dict[str, dict[str, Any]] = {}
        self._events: list[Any] = []

    @property
    def metrics(self) -> ExecutionMetrics:
        """Return the metrics tracker."""
        return self._metrics

    @property
    def events(self) -> list[Any]:
        """Return emitted domain events."""
        return self._events

    async def execute(self, request: BrainRequest) -> BrainResponse:
        """Execute the full brain pipeline for a request.

        Builds a default plan from the request and executes it.

        Args:
            request: The brain request.

        Returns:
            A BrainResponse with the generated content.
        """
        plan = self._build_default_plan(request)
        return await self.execute_plan(plan, request)

    async def execute_stream(self, request: BrainRequest) -> AsyncIterator[str]:
        """Stream the brain pipeline execution.

        Executes the plan and yields the response content in chunks.

        Args:
            request: The brain request.

        Yields:
            String tokens/chunks as they are generated.
        """
        response = await self.execute(request)

        async def _generate() -> AsyncIterator[str]:
            # Yield content in chunks
            chunk_size = 50
            content = response.content
            for i in range(0, len(content), chunk_size):
                yield content[i : i + chunk_size]
                await asyncio.sleep(0)  # Allow event loop to process

        return _generate()

    async def get_session_context(self, session_id: str) -> dict[str, Any]:
        """Retrieve full context for a session.

        Args:
            session_id: The session identifier.

        Returns:
            Session context dictionary.
        """
        return self._sessions.get(
            session_id,
            {
                "session_id": session_id,
                "history": [],
                "active": True,
            },
        )

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        request: BrainRequest,
    ) -> BrainResponse:
        """Execute a pre-built execution plan.

        Main orchestration logic:
        1. Initialize state manager
        2. Execute via scheduler
        3. Handle failures (retry, replan, recover)
        4. Apply reflection loop
        5. Aggregate results

        Args:
            plan: The execution plan to execute.
            request: The original brain request.

        Returns:
            A BrainResponse with the execution result.
        """
        self._reflection_engine.reset()

        # Emit execution started event
        self._emit_event(
            ExecutionStartedEvent(
                plan_id=plan.plan_id,
                intent=plan.intent,
                steps_count=len(plan.steps),
            )
        )

        state_manager = ExecutionStateManager(plan)
        await state_manager.start_execution()

        # Execute the plan
        results = await self._scheduler.execute_plan(plan, state_manager)

        # Check for failures
        has_failures = any(r.state == StepState.FAILED for r in results)

        if has_failures:
            response = await self._handle_failure(plan, results, request, state_manager)
        else:
            await state_manager.complete_execution()
            response = self._result_aggregator.aggregate(results, plan, request.session_id)

        # Apply reflection loop
        response = await self._apply_reflection(response, plan, results, request)

        # Record metrics
        success = state_manager.context.state == ExecutionState.COMPLETED
        self._metrics.record_execution(plan, results, success)

        # Update session context
        self._update_session(request, response)

        # Emit completion event
        if success:
            self._emit_event(
                ExecutionCompletedEvent(
                    plan_id=plan.plan_id,
                    total_latency_ms=response.latency_ms,
                    tokens_in=response.tokens.get("input", 0),
                    tokens_out=response.tokens.get("output", 0),
                )
            )
        else:
            self._emit_event(
                ExecutionFailedEvent(
                    plan_id=plan.plan_id,
                    error="; ".join(state_manager.context.errors[-3:]),
                    steps_completed=state_manager.get_completed_count(),
                )
            )

        return response

    async def _handle_failure(
        self,
        plan: ExecutionPlan,
        results: list[Any],
        request: BrainRequest,
        state_manager: ExecutionStateManager,
    ) -> BrainResponse:
        """Handle execution failure with recovery strategies.

        Args:
            plan: The failed plan.
            results: Step results.
            request: Original request.
            state_manager: State manager.

        Returns:
            A BrainResponse (either from recovery or error).
        """
        failure_type = self._failure_recovery.classify_failure(results, plan)
        action = self._failure_recovery.recommend_action(failure_type, results, plan)

        logger.info(
            "handling_failure",
            plan_id=plan.plan_id,
            failure_type=failure_type,
            action=action,
        )

        match action:
            case RecoveryAction.REPLAN:
                # Attempt replanning
                await state_manager.mark_replanning()
                new_plan = self._replanner.replan(plan, results)
                if new_plan:
                    return await self.execute_plan(new_plan, request)
                # Fall through to error response
                await state_manager.fail_execution("Replanning failed")

            case RecoveryAction.RETRY_DIFFERENT_PROVIDER | RecoveryAction.RETRY_DIFFERENT_MODEL:
                # Try replanning with different model/provider
                new_plan = self._replanner.replan(plan, results)
                if new_plan:
                    return await self.execute_plan(new_plan, request)
                await state_manager.fail_execution("No fallback available")

            case RecoveryAction.USE_PARTIAL_RESULTS:
                # Use whatever we have
                await state_manager.complete_execution()
                return self._result_aggregator.aggregate(results, plan, request.session_id)

            case RecoveryAction.FAIL_WITH_ERROR:
                await state_manager.fail_execution("Unrecoverable error")

            case _:
                await state_manager.fail_execution("Unknown recovery action")

        return self._failure_recovery.create_error_response(
            plan, results, request.session_id, failure_type
        )

    async def _apply_reflection(
        self,
        response: BrainResponse,
        plan: ExecutionPlan,
        results: list[Any],
        request: BrainRequest,
    ) -> BrainResponse:
        """Apply reflection loop to evaluate and potentially improve response.

        Args:
            response: Current response to evaluate.
            plan: Execution plan.
            results: Step results.
            request: Original request.

        Returns:
            The final (possibly improved) BrainResponse.
        """
        decision = self._reflection_engine.evaluate(response, plan, results)

        if decision == ReflectionDecision.ACCEPT:
            return response

        # Reflection wants a retry — modify plan parameters
        if decision == ReflectionDecision.RETRY_WITH_HIGHER_TEMP:
            # Increase temperature in plan params
            new_steps = []
            for step in plan.steps:
                if step.step_type == ExecutionStepType.LLM_CALL:
                    current_temp = step.params.get("temperature", 0.7)
                    new_temp = self._reflection_engine.get_adjusted_temperature(current_temp)
                    new_params = {**step.params, "temperature": new_temp}
                    new_step = ExecutionStep(
                        step_id=step.step_id,
                        step_type=step.step_type,
                        target=step.target,
                        params=new_params,
                        depends_on=step.depends_on,
                        timeout_seconds=step.timeout_seconds,
                        retryable=step.retryable,
                        priority=step.priority,
                    )
                    new_steps.append(new_step)
                else:
                    new_steps.append(step)

            new_plan = ExecutionPlan(
                plan_id=f"reflection-{plan.plan_id}",
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
            return await self.execute_plan(new_plan, request)

        # RETRY_WITH_DIFFERENT_MODEL
        new_plan = self._replanner.replan(plan, results)
        if new_plan:
            return await self.execute_plan(new_plan, request)

        # If replanning also fails, accept current response
        return response

    def _build_default_plan(self, request: BrainRequest) -> ExecutionPlan:
        """Build a default single-step LLM plan from a request.

        In production, this would call THALAMUS for plan generation.

        Args:
            request: The brain request.

        Returns:
            A default ExecutionPlan with one LLM step.
        """
        messages = request.messages
        last_content = messages[-1]["content"] if messages else ""

        return ExecutionPlan(
            plan_id=f"default-{request.session_id}",
            intent="general_conversation",
            steps=[
                ExecutionStep(
                    step_id="llm-main",
                    step_type=ExecutionStepType.LLM_CALL,
                    target=self._default_model,
                    params={
                        "messages": messages,
                        "prompt": last_content,
                        "temperature": 0.7,
                        "max_tokens_in": 100,
                        "max_tokens_out": 50,
                    },
                    depends_on=[],
                    timeout_seconds=30.0,
                    retryable=True,
                    priority=1,
                ),
            ],
            model_id=self._default_model,
            provider=self._default_provider,
            confidence=0.9,
            estimated_latency_ms=500,
            requires_streaming=request.stream,
        )

    def _update_session(self, request: BrainRequest, response: BrainResponse) -> None:
        """Update session context with the latest interaction.

        Args:
            request: The brain request.
            response: The generated response.
        """
        session_id = request.session_id
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "history": [],
                "active": True,
            }

        self._sessions[session_id]["history"].append(
            {
                "messages": request.messages,
                "response": response.content,
                "model": response.model_used,
            }
        )

    def _emit_event(self, event: Any) -> None:
        """Emit a domain event.

        Args:
            event: The domain event to emit.
        """
        self._events.append(event)
        logger.debug("event_emitted", event_type=type(event).__name__)
