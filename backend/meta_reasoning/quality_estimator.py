"""Meta Reasoning & Self Reflection Engine — quality estimation."""

from __future__ import annotations

from config.logging import get_logger
from meta_reasoning.schemas import EvidenceLabel, QualityReport, SimulationResult

logger = get_logger(__name__)


class QualityEstimator:
    """Estimates quality metrics for an execution plan."""

    def estimate(
        self,
        plan: dict,
        simulation: SimulationResult,
        evidence: dict[str, EvidenceLabel],
    ) -> QualityReport:
        """Estimate overall quality of a plan.

        Args:
            plan: The execution plan.
            simulation: Simulation results.
            evidence: Evidence labels from verification.

        Returns:
            QualityReport with all dimension scores.
        """
        correctness = self._score_correctness(plan, evidence)
        completeness = self._score_completeness(plan)
        safety = self._score_safety(plan, simulation)
        performance = self._score_performance(simulation)
        efficiency = self._score_efficiency(plan, simulation)
        cost_efficiency = self._score_cost_efficiency(simulation)
        confidence = self._score_confidence(evidence)
        explainability = self._score_explainability(plan)

        overall = (
            correctness * 0.20
            + completeness * 0.15
            + safety * 0.20
            + performance * 0.10
            + efficiency * 0.10
            + cost_efficiency * 0.10
            + confidence * 0.10
            + explainability * 0.05
        )

        report = QualityReport(
            correctness=correctness,
            completeness=completeness,
            safety=safety,
            performance=performance,
            efficiency=efficiency,
            cost_efficiency=cost_efficiency,
            confidence=confidence,
            explainability=explainability,
            overall=min(overall, 1.0),
            details={
                "weights": {
                    "correctness": 0.20,
                    "completeness": 0.15,
                    "safety": 0.20,
                    "performance": 0.10,
                    "efficiency": 0.10,
                    "cost_efficiency": 0.10,
                    "confidence": 0.10,
                    "explainability": 0.05,
                }
            },
        )
        logger.info("quality_estimated", overall=report.overall)
        return report

    def _score_correctness(self, plan: dict, evidence: dict[str, EvidenceLabel]) -> float:
        """Score how correct the plan is likely to be."""
        if not evidence:
            return 0.5
        verified_count = sum(1 for label in evidence.values() if label == EvidenceLabel.VERIFIED)
        total = len(evidence)
        return min(0.4 + (verified_count / max(total, 1)) * 0.6, 1.0)

    def _score_completeness(self, plan: dict) -> float:
        """Score how complete the plan specification is."""
        score = 0.3
        if plan.get("tasks"):
            score += 0.2
        if plan.get("execution_mode"):
            score += 0.1
        if plan.get("capabilities"):
            score += 0.1
        if plan.get("risk"):
            score += 0.1
        if plan.get("cost"):
            score += 0.1
        if plan.get("estimated_duration_ms", 0) > 0:
            score += 0.1
        return min(score, 1.0)

    def _score_safety(self, plan: dict, simulation: SimulationResult) -> float:
        """Score how safe the plan is."""
        risk_info = plan.get("risk", {})
        risk = risk_info.get("overall_risk", 0.5)
        failure_prob = simulation.failure_probability
        # Lower risk and failure probability = higher safety
        safety = 1.0 - ((risk + failure_prob) / 2.0)
        return float(max(min(safety, 1.0), 0.0))

    def _score_performance(self, simulation: SimulationResult) -> float:
        """Score expected performance of the plan."""
        latency = simulation.estimated_latency_ms
        # Under 1s is excellent, over 10s is poor
        if latency <= 1000:
            return 0.95
        if latency <= 5000:
            return 0.7
        if latency <= 10000:
            return 0.5
        return 0.3

    def _score_efficiency(self, plan: dict, simulation: SimulationResult) -> float:
        """Score execution efficiency."""
        tasks = plan.get("tasks", [])
        tokens = simulation.estimated_tokens
        if not tasks:
            return 0.5
        tokens_per_task = tokens / max(len(tasks), 1)
        # Under 300 tokens per task is very efficient
        if tokens_per_task <= 300:
            return 0.9
        if tokens_per_task <= 500:
            return 0.7
        return 0.5

    def _score_cost_efficiency(self, simulation: SimulationResult) -> float:
        """Score cost efficiency of execution."""
        cost = simulation.estimated_cost
        if cost <= 0.01:
            return 0.95
        if cost <= 0.05:
            return 0.8
        if cost <= 0.10:
            return 0.6
        return 0.4

    def _score_confidence(self, evidence: dict[str, EvidenceLabel]) -> float:
        """Score confidence based on evidence quality."""
        if not evidence:
            return 0.3

        weights: dict[EvidenceLabel, float] = {
            EvidenceLabel.VERIFIED: 1.0,
            EvidenceLabel.INFERRED: 0.7,
            EvidenceLabel.ESTIMATED: 0.5,
            EvidenceLabel.HYPOTHESIS: 0.2,
        }
        total = sum(weights.get(label, 0.3) for label in evidence.values())
        return min(total / len(evidence), 1.0)

    def _score_explainability(self, plan: dict) -> float:
        """Score how explainable the plan's decisions are."""
        score = 0.4
        if plan.get("execution_mode"):
            score += 0.2
        if plan.get("risk"):
            score += 0.2
        if plan.get("capabilities"):
            score += 0.2
        return min(score, 1.0)
