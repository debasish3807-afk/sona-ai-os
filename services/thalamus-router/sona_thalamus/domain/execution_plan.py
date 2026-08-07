"""Execution plan domain model — the primary output of THALAMUS.

An ExecutionPlan contains all information needed to execute a user's request
through the AI Kernel: the selected model, provider, ordered steps, and
estimated resource costs.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ExecutionStepType(StrEnum):
    """Types of steps that can appear in an execution plan."""

    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    AGENT_DELEGATION = "agent_delegation"
    MEMORY_RETRIEVAL = "memory_retrieval"
    KNOWLEDGE_QUERY = "knowledge_query"
    PARALLEL_GROUP = "parallel_group"
    CONDITIONAL = "conditional"


@dataclass(frozen=True)
class ExecutionStep:
    """A single step within an execution plan.

    Attributes:
        step_id: Unique identifier for this step.
        step_type: The type of execution this step performs.
        target: The model, tool, or agent name to invoke.
        params: Parameters to pass to the target.
        depends_on: List of step_ids that must complete before this step.
        timeout_seconds: Maximum time allowed for this step.
        retryable: Whether this step can be retried on failure.
        priority: Execution priority (lower = higher priority).
    """

    step_id: str
    step_type: ExecutionStepType
    target: str
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: float = 60.0
    retryable: bool = True
    priority: int = 5


@dataclass(frozen=True)
class ExecutionPlan:
    """The primary output of the THALAMUS router.

    Contains everything needed to execute a user request via the AI Kernel,
    including model selection, execution steps, cost estimates, and fallback info.

    Attributes:
        plan_id: Unique identifier for this plan.
        intent: The classified IntentCategory value.
        steps: Ordered list of execution steps.
        model_id: The selected model for the primary LLM call.
        provider: The selected provider for the model.
        context: Additional context data for execution.
        confidence: Classification confidence score (0.0-1.0).
        estimated_latency_ms: Predicted total latency in milliseconds.
        estimated_cost: Predicted cost in arbitrary units.
        requires_streaming: Whether the response should be streamed.
        fallback_plan_id: ID of an alternative plan if this one fails.
    """

    plan_id: str
    intent: str
    steps: list[ExecutionStep]
    model_id: str
    provider: str
    context: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    estimated_latency_ms: int = 0
    estimated_cost: float = 0.0
    requires_streaming: bool = False
    fallback_plan_id: str | None = None
