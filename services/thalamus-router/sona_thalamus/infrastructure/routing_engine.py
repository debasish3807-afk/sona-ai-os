"""Main THALAMUS routing engine.

Orchestrates all classifiers, selectors, and policy evaluation to produce
routing decisions and execution plans. Implements ThalamusRouterPort.
"""

from typing import Any

import structlog

from sona_thalamus.application.ports import ThalamusRouterPort
from sona_thalamus.domain.events import (
    ExecutionPlanCreatedEvent,
    IntentClassifiedEvent,
    RoutingFailedEvent,
)
from sona_thalamus.domain.execution_plan import ExecutionPlan
from sona_thalamus.domain.models import IntentCategory, RequestPriority, RoutingDecision
from sona_thalamus.domain.policies import PolicyAction
from sona_thalamus.infrastructure.agent_selector import AgentSelector
from sona_thalamus.infrastructure.context_builder import ContextBuilder
from sona_thalamus.infrastructure.execution_planner import ExecutionPlanner
from sona_thalamus.infrastructure.intent_classifier import IntentClassifier
from sona_thalamus.infrastructure.model_selector import ModelSelector
from sona_thalamus.infrastructure.policy_engine import PolicyEngine
from sona_thalamus.infrastructure.rule_fallback import RuleFallback
from sona_thalamus.infrastructure.task_classifier import TaskClassifier
from sona_thalamus.infrastructure.tool_selector import ToolSelector

logger = structlog.get_logger(__name__)

# Intent to target service mapping
_INTENT_SERVICE_MAP: dict[IntentCategory, str] = {
    IntentCategory.CHAT: "brain-os",
    IntentCategory.CODE: "ai-engineering-os",
    IntentCategory.RESEARCH: "research-os",
    IntentCategory.AUTOMATION: "workflow-engine",
    IntentCategory.MEMORY: "memory-os",
    IntentCategory.SYSTEM: "system-admin",
}

# Intent to fallback service mapping
_FALLBACK_SERVICE_MAP: dict[IntentCategory, str] = {
    IntentCategory.CHAT: "brain-os",
    IntentCategory.CODE: "brain-os",
    IntentCategory.RESEARCH: "brain-os",
    IntentCategory.AUTOMATION: "brain-os",
    IntentCategory.MEMORY: "brain-os",
    IntentCategory.SYSTEM: "brain-os",
}

# Intent to priority mapping
_INTENT_PRIORITY_MAP: dict[IntentCategory, RequestPriority] = {
    IntentCategory.CHAT: RequestPriority.NORMAL,
    IntentCategory.CODE: RequestPriority.HIGH,
    IntentCategory.RESEARCH: RequestPriority.NORMAL,
    IntentCategory.AUTOMATION: RequestPriority.HIGH,
    IntentCategory.MEMORY: RequestPriority.LOW,
    IntentCategory.SYSTEM: RequestPriority.CRITICAL,
}


class RoutingEngine(ThalamusRouterPort):
    """Main THALAMUS routing engine implementing ThalamusRouterPort.

    Orchestrates intent classification, task classification, model selection,
    tool/agent selection, context building, and execution planning to produce
    complete routing decisions and execution plans.
    """

    def __init__(
        self,
        intent_classifier: IntentClassifier,
        task_classifier: TaskClassifier,
        model_selector: ModelSelector,
        tool_selector: ToolSelector,
        agent_selector: AgentSelector,
        context_builder: ContextBuilder,
        execution_planner: ExecutionPlanner,
        policy_engine: PolicyEngine,
        rule_fallback: RuleFallback,
        confidence_threshold: float = 0.15,
    ) -> None:
        """Initialize the routing engine with all dependencies.

        Args:
            intent_classifier: Classifies user intent.
            task_classifier: Classifies task complexity.
            model_selector: Selects the optimal model.
            tool_selector: Selects required tools.
            agent_selector: Selects required agents.
            context_builder: Builds execution context.
            execution_planner: Builds execution plans.
            policy_engine: Evaluates routing policies.
            rule_fallback: Provides fallback plans.
            confidence_threshold: Minimum confidence for trusted classification.
        """
        self._intent_classifier = intent_classifier
        self._task_classifier = task_classifier
        self._model_selector = model_selector
        self._tool_selector = tool_selector
        self._agent_selector = agent_selector
        self._context_builder = context_builder
        self._execution_planner = execution_planner
        self._policy_engine = policy_engine
        self._rule_fallback = rule_fallback
        self._confidence_threshold = confidence_threshold
        self._events: list[Any] = []

    async def classify_intent(self, content: str, context: dict[str, Any]) -> IntentCategory:
        """Classify the intent of incoming content.

        Args:
            content: The user's input text to classify.
            context: Additional contextual information.

        Returns:
            The classified IntentCategory.
        """
        intent, confidence = self._intent_classifier.classify(content)

        # Emit event
        event = IntentClassifiedEvent(
            content=content,
            intent=str(intent),
            confidence=confidence,
        )
        self._events.append(event)

        logger.info(
            "intent_classified",
            intent=str(intent),
            confidence=confidence,
            content_length=len(content),
        )

        return intent

    async def route(self, request: dict[str, Any]) -> RoutingDecision:
        """Determine routing for a request.

        Produces a complete routing decision including target service,
        intent, priority, required agents, and fallback options.

        Args:
            request: The request payload containing content, context, etc.

        Returns:
            A RoutingDecision with all routing information.
        """
        content = str(request.get("content", ""))
        request.get("context", {})

        try:
            # Step 1: Classify intent
            intent, confidence = self._intent_classifier.classify(content)

            # Step 2: Check policies
            policy_action = self._policy_engine.get_effective_action(intent, content)
            if policy_action == PolicyAction.DENY:
                logger.warning("routing_denied", intent=str(intent), content_length=len(content))
                return RoutingDecision(
                    target_service="blocked",
                    intent=intent,
                    priority=RequestPriority.LOW,
                    requires_agents=[],
                    estimated_latency_ms=0,
                )

            # Step 3: Classify task
            task = self._task_classifier.classify(content, intent)

            # Step 4: Select agents
            agents = self._agent_selector.select(intent, task)

            # Step 5: Determine target service and priority
            target_service = _INTENT_SERVICE_MAP.get(intent, "brain-os")
            priority = _INTENT_PRIORITY_MAP.get(intent, RequestPriority.NORMAL)
            fallback_service = _FALLBACK_SERVICE_MAP.get(intent, "brain-os")

            # Step 6: Estimate latency
            estimated_latency = self._estimate_latency(intent, task.complexity_score)

            # Handle policy redirect
            if policy_action == PolicyAction.REDIRECT:
                # Policy engine would set a redirect target
                pass

            decision = RoutingDecision(
                target_service=target_service,
                intent=intent,
                priority=priority,
                requires_agents=agents,
                estimated_latency_ms=estimated_latency,
                fallback_service=fallback_service if fallback_service != target_service else None,
            )

            logger.info(
                "routing_decision_made",
                target=target_service,
                intent=str(intent),
                priority=str(priority),
                agents=agents,
            )

            return decision

        except Exception as e:
            # Emit failure event
            event = RoutingFailedEvent(content=content, error=str(e))
            self._events.append(event)
            logger.error("routing_failed", error=str(e), content_length=len(content))

            # Return safe fallback
            return RoutingDecision(
                target_service="brain-os",
                intent=IntentCategory.CHAT,
                priority=RequestPriority.NORMAL,
                requires_agents=[],
                estimated_latency_ms=2000,
                fallback_service=None,
            )

    async def health_check(self) -> dict[str, bool]:
        """Check health of all downstream services.

        Returns:
            Dictionary mapping service names to their health status.
        """
        # In a real implementation, this would ping downstream services
        services = list(_INTENT_SERVICE_MAP.values())
        return dict.fromkeys(services, True)

    async def create_execution_plan(self, request: dict[str, Any]) -> ExecutionPlan:
        """Create a full execution plan for the request.

        This is the primary THALAMUS output — a complete plan containing
        all information needed to execute via the AI Kernel.

        Args:
            request: The request payload containing content, context, etc.

        Returns:
            A complete ExecutionPlan.
        """
        content = str(request.get("content", ""))
        context_data = request.get("context", {})
        session_id = str(request.get("session_id", ""))

        try:
            # Step 1: Classify intent
            intent, confidence = self._intent_classifier.classify(content)

            # Step 2: Check if confidence is too low → use fallback
            if confidence < self._confidence_threshold:
                plan = self._rule_fallback.create_fallback_plan(
                    content=content,
                    confidence=confidence,
                    session_id=session_id,
                )
                return plan

            # Step 3: Check policies
            policy_action = self._policy_engine.get_effective_action(intent, content)
            if policy_action == PolicyAction.DENY:
                logger.warning("plan_creation_denied", intent=str(intent))
                return self._rule_fallback.create_fallback_plan(
                    content=content,
                    confidence=confidence,
                    session_id=session_id,
                )

            # Step 4: Classify task
            task = self._task_classifier.classify(content, intent)

            # Step 5: Build context
            full_request = {"content": content, "session_id": session_id, "context": context_data}
            exec_context = self._context_builder.build(full_request, intent)

            # Step 6: Select model
            model_config = self._model_selector.select(task, intent)

            # Step 7: Select tools
            tools = self._tool_selector.select(content, intent)

            # Step 8: Select agents
            agents = self._agent_selector.select(intent, task)

            # Step 9: Build execution plan
            plan = self._execution_planner.build_plan(
                intent=intent,
                task=task,
                context=exec_context,
                model_id=model_config.model_id,
                provider=model_config.provider,
                tools=tools,
                agents=agents,
                confidence=confidence,
            )

            # Emit event
            event = ExecutionPlanCreatedEvent(
                plan_id=plan.plan_id,
                intent=str(intent),
                model_id=model_config.model_id,
                steps_count=len(plan.steps),
            )
            self._events.append(event)

            logger.info(
                "execution_plan_created",
                plan_id=plan.plan_id,
                intent=str(intent),
                model=model_config.model_id,
                steps=len(plan.steps),
            )

            return plan

        except Exception as e:
            logger.error("plan_creation_failed", error=str(e))
            event = RoutingFailedEvent(content=content, error=str(e))
            self._events.append(event)

            return self._rule_fallback.create_fallback_plan(
                content=content,
                confidence=0.0,
                session_id=session_id,
            )

    def get_events(self) -> list[Any]:
        """Retrieve and clear accumulated domain events.

        Returns:
            List of domain events emitted since last retrieval.
        """
        events = self._events.copy()
        self._events.clear()
        return events

    def _estimate_latency(self, intent: IntentCategory, complexity: float) -> int:
        """Estimate request latency in milliseconds."""
        base_latencies: dict[IntentCategory, int] = {
            IntentCategory.CHAT: 200,
            IntentCategory.CODE: 500,
            IntentCategory.RESEARCH: 800,
            IntentCategory.AUTOMATION: 600,
            IntentCategory.MEMORY: 100,
            IntentCategory.SYSTEM: 50,
        }
        base = base_latencies.get(intent, 300)
        # Scale by complexity
        return int(base * (1 + complexity))
