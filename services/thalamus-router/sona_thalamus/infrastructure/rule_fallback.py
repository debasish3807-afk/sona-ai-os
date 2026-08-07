"""Rule-based fallback for low-confidence classifications.

When the intent classifier confidence is too low to trust, this module
provides a safe default execution plan using general-purpose settings.
"""

from uuid import uuid4

import structlog

from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType
from sona_thalamus.domain.models import IntentCategory

logger = structlog.get_logger(__name__)


class RuleFallback:
    """Provides fallback execution plans for low-confidence scenarios.

    When classification confidence is below threshold, generates a
    safe default plan using a general-purpose model with minimal tooling.
    """

    def __init__(
        self,
        default_model: str = "llama3.2",
        default_provider: str = "ollama",
        default_token_budget: int = 2048,
    ) -> None:
        """Initialize the rule fallback.

        Args:
            default_model: The general-purpose model to fall back to.
            default_provider: The default provider.
            default_token_budget: Default token budget for fallback plans.
        """
        self._default_model = default_model
        self._default_provider = default_provider
        self._default_token_budget = default_token_budget

    def create_fallback_plan(
        self,
        content: str,
        confidence: float,
        session_id: str = "",
    ) -> ExecutionPlan:
        """Create a fallback execution plan.

        Generates a simple single-LLM-call plan suitable for
        general conversational responses.

        Args:
            content: The original user input.
            confidence: The classification confidence that triggered fallback.
            session_id: Optional session identifier.

        Returns:
            A simple ExecutionPlan for safe fallback handling.
        """
        plan_id = str(uuid4())

        # Single LLM call step — no tools, no agents
        llm_step = ExecutionStep(
            step_id=f"{plan_id}-llm",
            step_type=ExecutionStepType.LLM_CALL,
            target=self._default_model,
            params={
                "provider": self._default_provider,
                "token_budget": self._default_token_budget,
                "streaming": True,
                "temperature": 0.7,
            },
            timeout_seconds=60.0,
            retryable=True,
            priority=3,
        )

        plan = ExecutionPlan(
            plan_id=plan_id,
            intent=str(IntentCategory.CHAT),
            steps=[llm_step],
            model_id=self._default_model,
            provider=self._default_provider,
            context={
                "session_id": session_id,
                "fallback": True,
                "original_confidence": confidence,
                "task_type": "simple",
                "complexity": 0.0,
            },
            confidence=confidence,
            estimated_latency_ms=2000,
            estimated_cost=0.01,
            requires_streaming=True,
        )

        logger.info(
            "fallback_plan_created",
            plan_id=plan_id,
            confidence=confidence,
            model=self._default_model,
        )

        return plan
