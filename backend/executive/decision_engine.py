"""Executive Intelligence layer — decision engine for strategy selection."""

from __future__ import annotations

from config.logging import get_logger
from executive.exceptions import DecisionError
from executive.schemas import Decision, Goal, Strategy

logger = get_logger(__name__)


class DecisionEngine:
    """Evaluates strategies and makes optimal decisions."""

    def make_decision(
        self,
        strategies: list[Strategy],
        goal: Goal,
        constraints: dict | None = None,
    ) -> Decision:
        """Select the best strategy and produce a decision."""
        if not strategies:
            raise DecisionError("No strategies provided for decision")

        constraints = constraints or {}
        scored: list[tuple[Strategy, float]] = [
            (s, self._evaluate_strategy(s, goal, constraints)) for s in strategies
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        selected, best_score = scored[0]

        self._calculate_trade_offs(selected, strategies)
        trace = [
            f"Evaluated {len(strategies)} strategies",
            f"Best score: {best_score:.3f} ({selected.strategy_type.value})",
            f"Goal priority: {goal.priority.value}",
        ]

        decision = Decision(
            alternatives=strategies,
            selected=selected,
            reasoning=f"Selected {selected.strategy_type.value}: {selected.reasoning}",
            confidence=selected.estimated_confidence,
            risk=selected.risk_level,
            cost=selected.estimated_cost,
            latency_ms=selected.estimated_latency_ms,
            trace=trace,
        )
        logger.info(
            "decision_made",
            decision_id=decision.decision_id,
            selected_type=selected.strategy_type.value,
            confidence=decision.confidence,
        )
        return decision

    def _evaluate_strategy(self, strategy: Strategy, goal: Goal, constraints: dict) -> float:
        """Calculate a composite score for a strategy."""
        confidence_weight = 0.35
        risk_weight = 0.25
        cost_weight = 0.20
        latency_weight = 0.20

        # Priority adjustments
        if goal.priority.value == "critical":
            confidence_weight = 0.4
            risk_weight = 0.3
        elif goal.priority.value == "low":
            cost_weight = 0.35

        # Budget constraint
        max_cost = constraints.get("max_cost", float("inf"))
        if strategy.estimated_cost > max_cost:
            return 0.0

        # Latency constraint
        max_latency = constraints.get("max_latency_ms", float("inf"))
        if strategy.estimated_latency_ms > max_latency:
            return 0.0

        score = (
            strategy.estimated_confidence * confidence_weight
            + (1.0 - strategy.risk_level) * risk_weight
            + (1.0 - min(strategy.estimated_cost, 1.0)) * cost_weight
            + (1.0 - min(strategy.estimated_latency_ms / 10000.0, 1.0)) * latency_weight
        )
        return score

    def _calculate_trade_offs(self, selected: Strategy, alternatives: list[Strategy]) -> list[str]:
        """Calculate trade-offs of the selected strategy versus alternatives."""
        trade_offs: list[str] = []
        for alt in alternatives:
            if alt.strategy_id == selected.strategy_id:
                continue
            if alt.estimated_confidence > selected.estimated_confidence:
                trade_offs.append(
                    f"{alt.strategy_type.value} has higher confidence "
                    f"({alt.estimated_confidence:.2f} vs {selected.estimated_confidence:.2f})"
                )
            if alt.estimated_cost < selected.estimated_cost:
                trade_offs.append(
                    f"{alt.strategy_type.value} is cheaper "
                    f"({alt.estimated_cost:.4f} vs {selected.estimated_cost:.4f})"
                )
            if alt.estimated_latency_ms < selected.estimated_latency_ms:
                trade_offs.append(
                    f"{alt.strategy_type.value} is faster "
                    f"({alt.estimated_latency_ms:.0f}ms vs {selected.estimated_latency_ms:.0f}ms)"
                )
        return trade_offs

    def explain_decision(self, decision: Decision) -> str:
        """Generate a human-readable explanation of a decision."""
        if decision.selected is None:
            return "No strategy was selected."
        lines = [
            f"Decision: {decision.reasoning}",
            f"Confidence: {decision.confidence:.1%}",
            f"Risk: {decision.risk:.1%}",
            f"Estimated Cost: ${decision.cost:.4f}",
            f"Estimated Latency: {decision.latency_ms:.0f}ms",
            f"Alternatives Considered: {len(decision.alternatives)}",
        ]
        if decision.trace:
            lines.append(f"Trace: {' → '.join(decision.trace)}")
        return "\n".join(lines)
