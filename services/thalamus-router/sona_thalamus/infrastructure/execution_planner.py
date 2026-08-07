"""Execution plan builder.

Assembles ExecutionPlan instances by combining intent classification,
task type, context, and model selection into ordered execution steps.
"""

from typing import Any
from uuid import uuid4

import structlog

from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType
from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.context_builder import ExecutionContext
from sona_thalamus.infrastructure.execution_graph import ExecutionGraph
from sona_thalamus.infrastructure.task_classifier import TaskClassification

logger = structlog.get_logger(__name__)

# Latency estimates (ms) per step type
_LATENCY_ESTIMATES: dict[ExecutionStepType, int] = {
    ExecutionStepType.LLM_CALL: 2000,
    ExecutionStepType.TOOL_CALL: 500,
    ExecutionStepType.AGENT_DELEGATION: 3000,
    ExecutionStepType.MEMORY_RETRIEVAL: 200,
    ExecutionStepType.KNOWLEDGE_QUERY: 800,
    ExecutionStepType.PARALLEL_GROUP: 1500,
    ExecutionStepType.CONDITIONAL: 100,
}

# Cost estimates (arbitrary units) per step type
_COST_ESTIMATES: dict[ExecutionStepType, float] = {
    ExecutionStepType.LLM_CALL: 0.01,
    ExecutionStepType.TOOL_CALL: 0.002,
    ExecutionStepType.AGENT_DELEGATION: 0.03,
    ExecutionStepType.MEMORY_RETRIEVAL: 0.001,
    ExecutionStepType.KNOWLEDGE_QUERY: 0.005,
    ExecutionStepType.PARALLEL_GROUP: 0.02,
    ExecutionStepType.CONDITIONAL: 0.0,
}


class ExecutionPlanner:
    """Builds ExecutionPlan instances from classification results.

    Combines intent, task classification, execution context, and
    model/tool/agent selections into a coherent execution plan with
    proper step ordering and dependency management.
    """

    def build_plan(
        self,
        intent: IntentCategory,
        task: TaskClassification,
        context: ExecutionContext,
        model_id: str,
        provider: str,
        tools: list[str],
        agents: list[str],
        confidence: float,
    ) -> ExecutionPlan:
        """Build a complete execution plan.

        Args:
            intent: The classified intent category.
            task: Task classification result.
            context: Assembled execution context.
            model_id: Selected model identifier.
            provider: Selected provider name.
            tools: List of tool names to include.
            agents: List of agent types to include.
            confidence: Classification confidence score.

        Returns:
            A complete ExecutionPlan ready for execution.
        """
        plan_id = str(uuid4())
        steps: list[ExecutionStep] = []
        graph = ExecutionGraph()

        # Step 1: Memory retrieval (if needed)
        memory_step_id: str | None = None
        if context.needs_memory_retrieval:
            memory_step_id = f"{plan_id}-memory"
            step = ExecutionStep(
                step_id=memory_step_id,
                step_type=ExecutionStepType.MEMORY_RETRIEVAL,
                target="memory-os",
                params={
                    "session_id": context.session_id,
                    "history_depth": context.history_depth,
                },
                timeout_seconds=10.0,
                retryable=True,
                priority=1,
            )
            steps.append(step)
            graph.add_step(step)

        # Step 2: Knowledge query (if needed)
        knowledge_step_id: str | None = None
        if context.needs_knowledge_query:
            knowledge_step_id = f"{plan_id}-knowledge"
            step = ExecutionStep(
                step_id=knowledge_step_id,
                step_type=ExecutionStepType.KNOWLEDGE_QUERY,
                target="knowledge-os",
                params={"token_budget": context.token_budget // 4},
                timeout_seconds=15.0,
                retryable=True,
                priority=2,
            )
            steps.append(step)
            graph.add_step(step)

        # Step 3: Primary LLM call
        llm_step_id = f"{plan_id}-llm"
        llm_depends: list[str] = []
        if memory_step_id:
            llm_depends.append(memory_step_id)
        if knowledge_step_id:
            llm_depends.append(knowledge_step_id)

        llm_step = ExecutionStep(
            step_id=llm_step_id,
            step_type=ExecutionStepType.LLM_CALL,
            target=model_id,
            params={
                "provider": provider,
                "token_budget": context.token_budget,
                "streaming": task.requires_streaming,
                **context.user_preferences,
            },
            depends_on=llm_depends,
            timeout_seconds=60.0,
            retryable=True,
            priority=3,
        )
        steps.append(llm_step)
        graph.add_step(llm_step)

        # Step 4: Tool calls (if any)
        for i, tool_name in enumerate(tools):
            tool_step_id = f"{plan_id}-tool-{i}"
            tool_step = ExecutionStep(
                step_id=tool_step_id,
                step_type=ExecutionStepType.TOOL_CALL,
                target=tool_name,
                params={},
                depends_on=[llm_step_id],
                timeout_seconds=30.0,
                retryable=True,
                priority=4,
            )
            steps.append(tool_step)
            graph.add_step(tool_step)

        # Step 5: Agent delegations (if any)
        for i, agent_type in enumerate(agents):
            agent_step_id = f"{plan_id}-agent-{i}"
            agent_step = ExecutionStep(
                step_id=agent_step_id,
                step_type=ExecutionStepType.AGENT_DELEGATION,
                target=agent_type,
                params={"model_id": model_id, "provider": provider},
                depends_on=[llm_step_id],
                timeout_seconds=120.0,
                retryable=True,
                priority=5,
            )
            steps.append(agent_step)
            graph.add_step(agent_step)

        # Estimate total latency and cost
        estimated_latency = self._estimate_latency(steps, graph)
        estimated_cost = self._estimate_cost(steps)

        # Build context dict for the plan
        plan_context: dict[str, Any] = {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "token_budget": context.token_budget,
            "task_type": str(task.task_type),
            "complexity": task.complexity_score,
        }
        plan_context.update(context.metadata)

        plan = ExecutionPlan(
            plan_id=plan_id,
            intent=str(intent),
            steps=steps,
            model_id=model_id,
            provider=provider,
            context=plan_context,
            confidence=confidence,
            estimated_latency_ms=estimated_latency,
            estimated_cost=estimated_cost,
            requires_streaming=task.requires_streaming,
        )

        logger.info(
            "execution_plan_built",
            plan_id=plan_id,
            intent=str(intent),
            steps_count=len(steps),
            estimated_latency_ms=estimated_latency,
            estimated_cost=estimated_cost,
        )

        return plan

    def _estimate_latency(self, steps: list[ExecutionStep], graph: ExecutionGraph) -> int:
        """Estimate total latency considering parallelism."""
        critical_path_seconds = graph.estimate_critical_path_latency()
        # Convert to milliseconds, use step estimates as fallback
        if critical_path_seconds > 0:
            return int(critical_path_seconds * 1000)

        # Fallback: sum individual step estimates
        total = sum(_LATENCY_ESTIMATES.get(s.step_type, 1000) for s in steps)
        return total

    def _estimate_cost(self, steps: list[ExecutionStep]) -> float:
        """Estimate total cost of all steps."""
        return sum(_COST_ESTIMATES.get(s.step_type, 0.001) for s in steps)
