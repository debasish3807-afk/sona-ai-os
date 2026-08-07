"""Result aggregator for Brain OS.

Combines results from multiple execution steps into a final BrainResponse,
aggregating token counts, latency, and selecting the primary output.
"""

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.domain.models import BrainResponse
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStepType

logger = structlog.get_logger()


class ResultAggregator:
    """Aggregates step results into a final BrainResponse.

    Identifies the primary LLM output, aggregates token counts from
    all LLM steps, computes total latency, and determines which model
    and agent were used.
    """

    def aggregate(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
        session_id: str,
    ) -> BrainResponse:
        """Combine step results into a BrainResponse.

        Args:
            results: All step results from execution.
            plan: The execution plan that was executed.
            session_id: Session identifier for the response.

        Returns:
            A BrainResponse with aggregated content and metrics.
        """
        # Find primary LLM output
        content = self._extract_primary_content(results, plan)

        # Aggregate token counts
        total_tokens_in, total_tokens_out = self._aggregate_tokens(results, plan)

        # Compute total latency
        total_latency = self._compute_total_latency(results)

        # Determine model used
        model_used = self._determine_model(results, plan)

        # Check for agent usage
        agent_used = self._extract_agent_used(results, plan)

        # Check for memory updates
        memory_updated = self._check_memory_updated(results, plan)

        logger.info(
            "results_aggregated",
            plan_id=plan.plan_id,
            content_length=len(content),
            tokens_in=total_tokens_in,
            tokens_out=total_tokens_out,
            total_latency_ms=total_latency,
        )

        return BrainResponse(
            content=content,
            session_id=session_id,
            model_used=model_used,
            tokens={"input": total_tokens_in, "output": total_tokens_out},
            latency_ms=total_latency,
            agent_used=agent_used,
            memory_updated=memory_updated,
        )

    def _extract_primary_content(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> str:
        """Extract the primary response content from LLM steps.

        Args:
            results: All step results.
            plan: The execution plan.

        Returns:
            The primary content string.
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}

        # Find completed LLM steps and take the last one's content
        llm_results = [
            r
            for r in results
            if r.state == StepState.COMPLETED
            and step_types.get(r.step_id) == ExecutionStepType.LLM_CALL
        ]

        if llm_results:
            last_llm = llm_results[-1]
            if isinstance(last_llm.output, dict):
                return str(last_llm.output.get("content", ""))
            return str(last_llm.output) if last_llm.output else ""

        # If no LLM results, use any completed step output
        completed = [r for r in results if r.state == StepState.COMPLETED and r.output]
        if completed:
            last = completed[-1]
            if isinstance(last.output, dict):
                return str(last.output.get("content", last.output.get("result", "")))
            return str(last.output)

        return ""

    def _aggregate_tokens(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> tuple[int, int]:
        """Aggregate token counts from all LLM steps.

        Args:
            results: All step results.
            plan: The execution plan.

        Returns:
            Tuple of (total_tokens_in, total_tokens_out).
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}
        total_in = 0
        total_out = 0

        for result in results:
            if (
                result.state == StepState.COMPLETED
                and step_types.get(result.step_id) == ExecutionStepType.LLM_CALL
                and isinstance(result.output, dict)
            ):
                total_in += result.output.get("tokens_in", 0)
                total_out += result.output.get("tokens_out", 0)

        return total_in, total_out

    def _compute_total_latency(self, results: list[StepResult]) -> float:
        """Compute total execution latency across all steps.

        Args:
            results: All step results.

        Returns:
            Total latency in milliseconds.
        """
        return sum(r.latency_ms for r in results)

    def _determine_model(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> str:
        """Determine the primary model used.

        Args:
            results: All step results.
            plan: The execution plan.

        Returns:
            Model identifier string.
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}

        # Look for model info in LLM step outputs
        for result in results:
            if (
                result.state == StepState.COMPLETED
                and step_types.get(result.step_id) == ExecutionStepType.LLM_CALL
                and isinstance(result.output, dict)
                and "model" in result.output
            ):
                return str(result.output["model"])

        # Fall back to plan's model_id
        return str(plan.model_id)

    def _extract_agent_used(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> str | None:
        """Extract which agent was used (if any).

        Args:
            results: All step results.
            plan: The execution plan.

        Returns:
            Agent name if used, None otherwise.
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}

        for result in results:
            if (
                result.state == StepState.COMPLETED
                and step_types.get(result.step_id) == ExecutionStepType.AGENT_DELEGATION
                and isinstance(result.output, dict)
            ):
                return str(result.output.get("agent", ""))

        return None

    def _check_memory_updated(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> bool:
        """Check if memory was updated during execution.

        Args:
            results: All step results.
            plan: The execution plan.

        Returns:
            True if a memory step completed successfully.
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}

        return any(
            result.state == StepState.COMPLETED
            and step_types.get(result.step_id) == ExecutionStepType.MEMORY_RETRIEVAL
            for result in results
        )
