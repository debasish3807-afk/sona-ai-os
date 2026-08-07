"""Dependency injection factory for the THALAMUS router.

Assembles the complete routing engine with all dependencies wired together.
"""

import structlog

from sona_thalamus.infrastructure.agent_selector import AgentSelector
from sona_thalamus.infrastructure.confidence_scorer import ConfidenceScorer
from sona_thalamus.infrastructure.context_builder import ContextBuilder
from sona_thalamus.infrastructure.execution_planner import ExecutionPlanner
from sona_thalamus.infrastructure.intent_classifier import IntentClassifier
from sona_thalamus.infrastructure.model_selector import ModelSelector
from sona_thalamus.infrastructure.policy_engine import PolicyEngine
from sona_thalamus.infrastructure.routing_engine import RoutingEngine
from sona_thalamus.infrastructure.rule_fallback import RuleFallback
from sona_thalamus.infrastructure.task_classifier import TaskClassifier
from sona_thalamus.infrastructure.tool_selector import ToolSelector

logger = structlog.get_logger(__name__)


def create_thalamus_router(
    default_model: str = "llama3.2",
    default_provider: str = "ollama",
    confidence_threshold: float = 0.15,
) -> RoutingEngine:
    """Create a fully assembled THALAMUS routing engine.

    Wires together all classifiers, selectors, and engines with
    the specified configuration.

    Args:
        default_model: The default model ID for fallback scenarios.
        default_provider: The default provider for fallback scenarios.
        confidence_threshold: Minimum confidence for trusted classification.

    Returns:
        A fully configured RoutingEngine instance.
    """
    # Build confidence scorer
    scorer = ConfidenceScorer()

    # Build classifiers
    intent_classifier = IntentClassifier(
        confidence_threshold=confidence_threshold,
        scorer=scorer,
    )
    task_classifier = TaskClassifier()

    # Build selectors
    model_selector = ModelSelector(
        default_model=default_model,
        default_provider=default_provider,
    )
    tool_selector = ToolSelector()
    agent_selector = AgentSelector()

    # Build supporting components
    context_builder = ContextBuilder()
    execution_planner = ExecutionPlanner()
    policy_engine = PolicyEngine()
    rule_fallback = RuleFallback(
        default_model=default_model,
        default_provider=default_provider,
    )

    # Assemble the routing engine
    engine = RoutingEngine(
        intent_classifier=intent_classifier,
        task_classifier=task_classifier,
        model_selector=model_selector,
        tool_selector=tool_selector,
        agent_selector=agent_selector,
        context_builder=context_builder,
        execution_planner=execution_planner,
        policy_engine=policy_engine,
        rule_fallback=rule_fallback,
        confidence_threshold=confidence_threshold,
    )

    logger.info(
        "thalamus_router_created",
        default_model=default_model,
        default_provider=default_provider,
        confidence_threshold=confidence_threshold,
    )

    return engine
