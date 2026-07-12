"""Executive Intelligence layer — main orchestrator brain."""

from __future__ import annotations

from config.logging import get_logger
from executive.approval_engine import ApprovalEngine
from executive.capability_orchestrator import CapabilityOrchestrator
from executive.confidence_engine import ConfidenceEngine
from executive.cost_engine import CostEngine
from executive.decision_engine import DecisionEngine
from executive.events import ExecutiveEvent, ExecutiveEventType
from executive.exceptions import ExecutiveError
from executive.execution_planner import ExecutionPlanner
from executive.goal_manager import GoalManager
from executive.model_selector import ModelSelector
from executive.parallel_planner import ParallelPlanner
from executive.provider_selector import ProviderSelector
from executive.risk_engine import RiskEngine
from executive.schemas import GoalPriority
from executive.strategic_planner import StrategicPlanner
from executive.workflow_optimizer import WorkflowOptimizer

logger = get_logger(__name__)


class ExecutiveBrain:
    """Main orchestrator for the executive intelligence layer.

    Coordinates goal management, strategic planning, decision-making,
    execution planning, risk assessment, and approval workflows.
    """

    def __init__(
        self,
        goal_manager: GoalManager,
        strategic_planner: StrategicPlanner,
        decision_engine: DecisionEngine,
        execution_planner: ExecutionPlanner,
        risk_engine: RiskEngine,
        cost_engine: CostEngine,
        confidence_engine: ConfidenceEngine,
        capability_orchestrator: CapabilityOrchestrator,
        provider_selector: ProviderSelector,
        model_selector: ModelSelector,
        workflow_optimizer: WorkflowOptimizer,
        parallel_planner: ParallelPlanner,
        approval_engine: ApprovalEngine,
    ) -> None:
        self._goal_manager = goal_manager
        self._strategic_planner = strategic_planner
        self._decision_engine = decision_engine
        self._execution_planner = execution_planner
        self._risk_engine = risk_engine
        self._cost_engine = cost_engine
        self._confidence_engine = confidence_engine
        self._capability_orchestrator = capability_orchestrator
        self._provider_selector = provider_selector
        self._model_selector = model_selector
        self._workflow_optimizer = workflow_optimizer
        self._parallel_planner = parallel_planner
        self._approval_engine = approval_engine
        self._events: list[ExecutiveEvent] = []

    async def process_goal(
        self,
        title: str,
        description: str,
        priority: GoalPriority = GoalPriority.MEDIUM,
        constraints: dict | None = None,
    ) -> dict:
        """Process a goal through the full executive pipeline."""
        constraints = constraints or {}

        try:
            # 1. Create goal
            goal = self._goal_manager.create_goal(title, description, priority)
            self._emit(ExecutiveEventType.GOAL_CREATED, goal.goal_id, {"title": title})

            # 2. Generate strategies
            available_caps = self._provider_selector.get_available_providers()
            strategies = self._strategic_planner.generate_strategies(
                goal, available_caps, constraints
            )
            self._emit(
                ExecutiveEventType.STRATEGY_GENERATED,
                goal.goal_id,
                {"count": len(strategies)},
            )

            # 3. Make decision
            decision = self._decision_engine.make_decision(strategies, goal, constraints)
            self._emit(
                ExecutiveEventType.DECISION_MADE,
                goal.goal_id,
                {"decision_id": decision.decision_id},
            )

            # 4. Create execution plan
            plan = self._execution_planner.create_plan(decision, goal)
            self._emit(
                ExecutiveEventType.EXECUTION_PLANNED,
                goal.goal_id,
                {"plan_id": plan.plan_id},
            )

            # 5. Assess risk
            risk = self._risk_engine.assess_risk(plan, goal)

            # 6. Estimate cost
            cost = self._cost_engine.estimate_cost(plan, plan.tasks)

            # 7. Estimate confidence
            confidence = self._confidence_engine.estimate_confidence(decision, plan)

            # 8. Get approval
            approval = self._approval_engine.evaluate(plan, risk, cost, confidence)
            if approval.value in ("auto_approved", "approved"):
                self._emit(
                    ExecutiveEventType.EXECUTION_APPROVED,
                    goal.goal_id,
                    {"approval": approval.value},
                )
            else:
                self._emit(
                    ExecutiveEventType.EXECUTION_REJECTED,
                    goal.goal_id,
                    {"approval": approval.value},
                )

            # 9. Optimize workflow
            optimized_plan = self._workflow_optimizer.optimize(plan)
            self._emit(
                ExecutiveEventType.EXECUTION_OPTIMIZED,
                goal.goal_id,
                {"plan_id": optimized_plan.plan_id},
            )

            # 10. Return complete result
            return {
                "goal": goal.to_dict(),
                "decision": decision.to_dict(),
                "plan": optimized_plan.to_dict(),
                "risk": risk,
                "cost": cost,
                "confidence": confidence,
                "approval": approval.value,
            }

        except ExecutiveError as exc:
            logger.error("executive_error", error=str(exc), title=title)
            raise
        except Exception as exc:
            logger.error("unexpected_executive_error", error=str(exc), title=title)
            raise ExecutiveError(str(exc), category="unexpected") from exc

    def get_status(self) -> dict:
        """Return current executive brain status."""
        metrics = self._goal_manager.get_metrics()
        return {
            "active": True,
            "goals": metrics,
            "events_count": len(self._events),
            "providers": self._provider_selector.get_available_providers(),
            "models": self._model_selector.get_available_models(),
        }

    def get_events(self) -> list[dict]:
        """Return all emitted events."""
        return [e.to_dict() for e in self._events]

    def _emit(self, event_type: ExecutiveEventType, goal_id: str, data: dict) -> None:
        """Emit an executive event."""
        event = ExecutiveEvent(event_type=event_type, goal_id=goal_id, data=data)
        self._events.append(event)
        logger.debug("event_emitted", event_type=event_type.value, goal_id=goal_id)
