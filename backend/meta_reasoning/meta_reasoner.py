"""Meta Reasoning & Self Reflection Engine — main orchestrator."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from meta_reasoning.alternative_generator import AlternativeGenerator
from meta_reasoning.counterfactual_engine import CounterfactualEngine
from meta_reasoning.critique_engine import CritiqueEngine
from meta_reasoning.evidence_engine import EvidenceEngine
from meta_reasoning.events import MetaReasoningEvent, MetaReasoningEventType
from meta_reasoning.exceptions import DeadlockError
from meta_reasoning.hypothesis_engine import HypothesisEngine
from meta_reasoning.plan_refiner import PlanRefiner
from meta_reasoning.plan_validator import PlanValidator
from meta_reasoning.quality_estimator import QualityEstimator
from meta_reasoning.reasoning_memory import ReasoningMemory
from meta_reasoning.reasoning_trace import ReasoningTrace
from meta_reasoning.reflection_engine import ReflectionEngine
from meta_reasoning.schemas import (
    QualityReport,
    ReasoningResult,
    ReasoningVerdict,
    SimulationResult,
)
from meta_reasoning.simulation_engine import SimulationEngine
from meta_reasoning.uncertainty_engine import UncertaintyEngine

logger = get_logger(__name__)


class MetaReasoner:
    """Main orchestrator for the meta-reasoning pipeline.

    Coordinates reflection, critique, simulation, evidence verification,
    and quality estimation to produce a final reasoning verdict.
    """

    def __init__(
        self,
        reflection_engine: ReflectionEngine,
        critique_engine: CritiqueEngine,
        alternative_generator: AlternativeGenerator,
        hypothesis_engine: HypothesisEngine,
        counterfactual_engine: CounterfactualEngine,
        simulation_engine: SimulationEngine,
        plan_validator: PlanValidator,
        plan_refiner: PlanRefiner,
        evidence_engine: EvidenceEngine,
        uncertainty_engine: UncertaintyEngine,
        quality_estimator: QualityEstimator,
        reasoning_memory: ReasoningMemory,
    ) -> None:
        self._reflection_engine = reflection_engine
        self._critique_engine = critique_engine
        self._alternative_generator = alternative_generator
        self._hypothesis_engine = hypothesis_engine
        self._counterfactual_engine = counterfactual_engine
        self._simulation_engine = simulation_engine
        self._plan_validator = plan_validator
        self._plan_refiner = plan_refiner
        self._evidence_engine = evidence_engine
        self._uncertainty_engine = uncertainty_engine
        self._quality_estimator = quality_estimator
        self._reasoning_memory = reasoning_memory
        self._events: list[MetaReasoningEvent] = []
        self._trace: ReasoningTrace = ReasoningTrace()

    async def reason(self, plan: dict, goal: dict, context: dict) -> ReasoningResult:
        """Run the full meta-reasoning pipeline on a plan.

        Args:
            plan: The execution plan to reason about.
            goal: The goal the plan should achieve.
            context: Environment context.

        Returns:
            ReasoningResult with verdict and supporting analysis.

        Raises:
            DeadlockError: If refinement loop exceeds max iterations.
        """
        plan_id = plan.get("plan_id", "unknown")
        self._trace.clear()
        max_iterations = 3
        iteration = 0

        self._emit(MetaReasoningEventType.REFLECTION_STARTED, plan_id)

        # 1. Validate plan
        valid, issues = self._plan_validator.validate(plan, context)
        self._trace.add("validation", "observation", f"Validation: valid={valid}, issues={len(issues)}")

        if not valid and len(issues) > 5:
            self._emit(MetaReasoningEventType.PLAN_REJECTED, plan_id, {"issues": issues})
            return ReasoningResult(
                verdict=ReasoningVerdict.REJECTED,
                confidence=0.9,
                risk=1.0,
                quality_score=0.0,
                critique=issues,
                reasoning_trace=self._trace.get_summary(),
                explanation="Plan failed validation with critical issues",
            )

        # 2. Reflect on plan
        reflection = self._reflection_engine.reflect(plan, goal, context)
        self._trace.add("reflection", "observation", f"Reflection overall: {reflection['overall']:.2f}")
        self._emit(MetaReasoningEventType.REFLECTION_COMPLETED, plan_id, reflection)

        # 3. Generate critique
        critiques = self._critique_engine.critique(plan, reflection)
        self._trace.add("critique", "critique", f"Generated {len(critiques)} critique points")
        self._emit(MetaReasoningEventType.CRITIQUE_GENERATED, plan_id, {"critiques": critiques})

        # 4. Verify evidence
        evidence = self._evidence_engine.verify(plan, context)
        self._trace.add("evidence", "evidence", f"Verified {len(evidence)} evidence claims")
        self._emit(MetaReasoningEventType.EVIDENCE_VERIFIED, plan_id, {"evidence_count": len(evidence)})

        # 5. Counterfactual analysis
        counterfactuals = self._counterfactual_engine.analyze(plan, context)
        self._trace.add("counterfactual", "alternative", f"Explored {len(counterfactuals)} scenarios")

        # 6. Simulate execution
        self._emit(MetaReasoningEventType.SIMULATION_STARTED, plan_id)
        simulation = self._simulation_engine.simulate(plan, context)
        self._trace.add("simulation", "simulation", f"Simulation success={simulation.success}")
        self._emit(MetaReasoningEventType.SIMULATION_COMPLETED, plan_id, simulation.to_dict())

        # 7. Estimate quality
        quality = self._quality_estimator.estimate(plan, simulation, evidence)
        self._trace.add("quality", "observation", f"Quality overall: {quality.overall:.2f}")

        # 8. Uncertainty assessment
        uncertainty = self._uncertainty_engine.assess(plan, evidence, context)
        confidence = 1.0 - uncertainty.get("overall_uncertainty", 0.5)
        self._trace.add("confidence", "observation", f"Confidence: {confidence:.2f}")
        self._emit(MetaReasoningEventType.CONFIDENCE_UPDATED, plan_id, {"confidence": confidence})

        # 9. Refine if needed
        current_plan = plan
        while self._should_refine(quality, critiques) and iteration < max_iterations:
            iteration += 1
            self._trace.add("refinement", "improvement", f"Refinement iteration {iteration}")
            current_plan = self._plan_refiner.refine(current_plan, critiques, simulation, quality)
            self._emit(MetaReasoningEventType.PLAN_REFINED, plan_id, {"iteration": iteration})

            # Re-evaluate after refinement
            simulation = self._simulation_engine.simulate(current_plan, context)
            evidence = self._evidence_engine.verify(current_plan, context)
            quality = self._quality_estimator.estimate(current_plan, simulation, evidence)
            critiques = self._critique_engine.critique(current_plan, reflection)

            if iteration >= max_iterations and self._should_refine(quality, critiques):
                raise DeadlockError(
                    f"Refinement loop exceeded {max_iterations} iterations without convergence"
                )

        # 10. Make verdict
        verdict = self._make_verdict(quality, critiques, simulation, uncertainty)
        self._trace.add("decision", "decision", f"Verdict: {verdict.value}")

        # Generate alternatives count
        alternatives = self._alternative_generator.generate(plan, critiques, context)

        improvements = PlanRefiner.get_improvements(plan, current_plan)

        result = ReasoningResult(
            verdict=verdict,
            confidence=confidence,
            risk=simulation.failure_probability,
            quality_score=quality.overall,
            critique=critiques,
            improvements=improvements,
            evidence_labels=evidence,
            reasoning_trace=self._trace.get_summary(),
            alternatives_considered=len(alternatives),
            simulation_passed=simulation.success,
            iterations=iteration + 1,
            max_iterations=max_iterations,
            explanation=f"Meta-reasoning completed with verdict '{verdict.value}' after {iteration + 1} iteration(s)",
        )

        self._reasoning_memory.store(result, plan_id)
        self._emit(MetaReasoningEventType.REASONING_COMPLETED, plan_id, result.to_dict())

        logger.info("meta_reasoning_complete", verdict=verdict.value, plan_id=plan_id)
        return result

    def _make_verdict(
        self,
        quality: QualityReport,
        critiques: list[str],
        simulation: SimulationResult,
        uncertainty: dict,
    ) -> ReasoningVerdict:
        """Determine the final verdict based on all analysis.

        Args:
            quality: Quality report.
            critiques: Remaining critiques.
            simulation: Simulation result.
            uncertainty: Uncertainty assessment.

        Returns:
            The reasoning verdict.
        """
        overall_uncertainty = uncertainty.get("overall_uncertainty", 0.5)

        if not simulation.success and quality.safety < 0.3:
            return ReasoningVerdict.BLOCKED

        if overall_uncertainty > 0.8:
            return ReasoningVerdict.HUMAN_REQUIRED

        if quality.overall >= 0.7 and simulation.success and len(critiques) <= 2:
            return ReasoningVerdict.APPROVED

        if quality.overall < 0.4 or (not simulation.success and quality.safety < 0.5):
            return ReasoningVerdict.REJECTED

        return ReasoningVerdict.NEEDS_REFINEMENT

    def _should_refine(self, quality: QualityReport, critiques: list[str]) -> bool:
        """Determine whether the plan needs further refinement.

        Args:
            quality: Current quality report.
            critiques: Current critique list.

        Returns:
            True if refinement is warranted.
        """
        if quality.overall >= 0.7 and len(critiques) <= 2:
            return False
        if quality.overall < 0.6 or len(critiques) > 3:
            return True
        return False

    def get_status(self) -> dict[str, Any]:
        """Get current status of the meta-reasoner.

        Returns:
            Status dictionary.
        """
        return {
            "events_count": len(self._events),
            "trace_entries": len(self._trace.get_all()),
            "memory_stats": self._reasoning_memory.stats(),
            "active": True,
        }

    def _emit(
        self,
        event_type: MetaReasoningEventType,
        plan_id: str,
        data: dict | None = None,
    ) -> None:
        """Emit a meta-reasoning event."""
        event = MetaReasoningEvent(
            event_type=event_type,
            plan_id=plan_id,
            data=data or {},
        )
        self._events.append(event)
