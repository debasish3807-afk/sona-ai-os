"""Executive Intelligence layer — strategic planning for goal achievement."""

from __future__ import annotations

from config.logging import get_logger
from executive.schemas import Goal, Strategy, StrategyType

logger = get_logger(__name__)


class StrategicPlanner:
    """Generates and ranks execution strategies for goals."""

    def generate_strategies(
        self,
        goal: Goal,
        available_capabilities: list[str],
        constraints: dict | None = None,
    ) -> list[Strategy]:
        """Generate multiple strategies for achieving a goal."""
        constraints = constraints or {}
        strategies: list[Strategy] = [
            self._generate_fastest(goal, available_capabilities),
            self._generate_lowest_cost(goal, available_capabilities),
            self._generate_highest_quality(goal, available_capabilities),
            self._generate_safest(goal, available_capabilities),
            self._generate_balanced(goal, available_capabilities),
        ]
        logger.info(
            "strategies_generated",
            goal_id=goal.goal_id,
            count=len(strategies),
        )
        return strategies

    def _generate_fastest(self, goal: Goal, caps: list[str]) -> Strategy:
        """Generate a speed-optimized strategy."""
        steps = [f"parallel_execute:{cap}" for cap in caps[:3]]
        return Strategy(
            strategy_type=StrategyType.FASTEST,
            description=f"Fastest path to: {goal.title}",
            estimated_cost=len(caps) * 0.05,
            estimated_latency_ms=500.0 + len(steps) * 100.0,
            estimated_confidence=0.7,
            risk_level=0.4,
            steps=steps,
            trade_offs=["Higher cost", "Lower accuracy"],
            reasoning="Prioritizes speed over cost and quality.",
        )

    def _generate_lowest_cost(self, goal: Goal, caps: list[str]) -> Strategy:
        """Generate a cost-optimized strategy."""
        steps = [f"sequential_execute:{cap}" for cap in caps[:2]]
        return Strategy(
            strategy_type=StrategyType.LOWEST_COST,
            description=f"Cheapest path to: {goal.title}",
            estimated_cost=len(caps) * 0.01,
            estimated_latency_ms=2000.0 + len(steps) * 500.0,
            estimated_confidence=0.6,
            risk_level=0.3,
            steps=steps,
            trade_offs=["Slower execution", "Fewer capabilities used"],
            reasoning="Minimizes token and compute cost.",
        )

    def _generate_highest_quality(self, goal: Goal, caps: list[str]) -> Strategy:
        """Generate a quality-optimized strategy."""
        steps = [f"verify_execute:{cap}" for cap in caps]
        return Strategy(
            strategy_type=StrategyType.HIGHEST_QUALITY,
            description=f"Highest quality path to: {goal.title}",
            estimated_cost=len(caps) * 0.1,
            estimated_latency_ms=3000.0 + len(steps) * 300.0,
            estimated_confidence=0.9,
            risk_level=0.2,
            steps=steps,
            trade_offs=["Higher cost", "Longer execution time"],
            reasoning="Maximizes output quality with verification steps.",
        )

    def _generate_safest(self, goal: Goal, caps: list[str]) -> Strategy:
        """Generate a safety-optimized strategy."""
        steps = [f"safe_execute:{cap}" for cap in caps[:2]]
        return Strategy(
            strategy_type=StrategyType.SAFEST,
            description=f"Safest path to: {goal.title}",
            estimated_cost=len(caps) * 0.03,
            estimated_latency_ms=2500.0 + len(steps) * 400.0,
            estimated_confidence=0.8,
            risk_level=0.1,
            steps=steps,
            trade_offs=["Conservative approach", "May miss optimizations"],
            reasoning="Minimizes risk with conservative execution.",
        )

    def _generate_balanced(self, goal: Goal, caps: list[str]) -> Strategy:
        """Generate a balanced strategy."""
        steps = [f"balanced_execute:{cap}" for cap in caps[:3]]
        return Strategy(
            strategy_type=StrategyType.BALANCED,
            description=f"Balanced path to: {goal.title}",
            estimated_cost=len(caps) * 0.04,
            estimated_latency_ms=1500.0 + len(steps) * 200.0,
            estimated_confidence=0.75,
            risk_level=0.3,
            steps=steps,
            trade_offs=["No single metric optimized"],
            reasoning="Balances cost, speed, quality, and risk.",
        )

    def rank_strategies(self, strategies: list[Strategy]) -> list[Strategy]:
        """Rank strategies by composite score (higher is better)."""

        def _composite_score(s: Strategy) -> float:
            return (
                s.estimated_confidence * 0.4
                + (1.0 - s.risk_level) * 0.3
                + (1.0 / max(s.estimated_latency_ms, 1.0)) * 1000.0 * 0.15
                + (1.0 / max(s.estimated_cost, 0.001)) * 0.01 * 0.15
            )

        return sorted(strategies, key=_composite_score, reverse=True)
