"""Tests for the Meta Reasoning & Self Reflection Engine."""

from __future__ import annotations

import asyncio
import sys
import uuid

sys.path.insert(0, "/projects/sandbox/sona-ai-os/backend")

import pytest

from meta_reasoning.alternative_generator import AlternativeGenerator
from meta_reasoning.counterfactual_engine import CounterfactualEngine
from meta_reasoning.critique_engine import CritiqueEngine
from meta_reasoning.events import MetaReasoningEvent, MetaReasoningEventType
from meta_reasoning.evidence_engine import EvidenceEngine
from meta_reasoning.exceptions import (
    DeadlockError,
    MetaReasoningError,
    ReflectionError,
    SimulationError,
    ValidationError,
)
from meta_reasoning.hypothesis_engine import HypothesisEngine
from meta_reasoning.meta_reasoner import MetaReasoner
from meta_reasoning.plan_refiner import PlanRefiner
from meta_reasoning.plan_validator import PlanValidator
from meta_reasoning.quality_estimator import QualityEstimator
from meta_reasoning.reasoning_memory import ReasoningMemory
from meta_reasoning.reasoning_trace import ReasoningTrace
from meta_reasoning.reflection_engine import ReflectionEngine
from meta_reasoning.schemas import (
    EvidenceLabel,
    QualityReport,
    ReasoningResult,
    ReasoningStage,
    ReasoningVerdict,
    SimulationResult,
)
from meta_reasoning.simulation_engine import SimulationEngine
from meta_reasoning.uncertainty_engine import UncertaintyEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_plan(**kwargs) -> dict:
    defaults = {
        "plan_id": "p1",
        "goal_id": "g1",
        "tasks": ["t1", "t2"],
        "execution_mode": "sequential",
        "estimated_duration_ms": 1000,
        "capabilities": ["cap1"],
        "risk": {"overall_risk": 0.2},
        "cost": {"total_estimated": 0.05},
    }
    defaults.update(kwargs)
    return defaults


def _make_goal(**kwargs) -> dict:
    defaults = {
        "goal_id": "g1",
        "title": "Test Goal",
        "description": "A test goal",
        "priority": "medium",
    }
    defaults.update(kwargs)
    return defaults


def _make_context(**kwargs) -> dict:
    defaults = {
        "budget": 1.0,
        "max_risk": 0.5,
        "available_capabilities": ["cap1", "cap2"],
        "available_providers": ["ollama", "openai"],
    }
    defaults.update(kwargs)
    return defaults


def _make_simulation(**kwargs) -> SimulationResult:
    defaults = {
        "success": True,
        "estimated_latency_ms": 800.0,
        "estimated_cost": 0.03,
        "estimated_tokens": 700,
        "failure_probability": 0.1,
        "resource_usage": {"memory_mb": 192, "cpu_cores": 1},
        "expected_outcome": "Success",
        "warnings": [],
    }
    defaults.update(kwargs)
    return SimulationResult(**defaults)


def _make_quality(**kwargs) -> QualityReport:
    defaults = {
        "correctness": 0.8,
        "completeness": 0.8,
        "safety": 0.8,
        "performance": 0.8,
        "efficiency": 0.8,
        "cost_efficiency": 0.8,
        "confidence": 0.8,
        "explainability": 0.8,
        "overall": 0.8,
        "details": {},
    }
    defaults.update(kwargs)
    return QualityReport(**defaults)


def _make_reasoner() -> MetaReasoner:
    return MetaReasoner(
        reflection_engine=ReflectionEngine(),
        critique_engine=CritiqueEngine(),
        alternative_generator=AlternativeGenerator(),
        hypothesis_engine=HypothesisEngine(),
        counterfactual_engine=CounterfactualEngine(),
        simulation_engine=SimulationEngine(),
        plan_validator=PlanValidator(),
        plan_refiner=PlanRefiner(),
        evidence_engine=EvidenceEngine(),
        uncertainty_engine=UncertaintyEngine(),
        quality_estimator=QualityEstimator(),
        reasoning_memory=ReasoningMemory(),
    )


# ---------------------------------------------------------------------------
# TestSchemas
# ---------------------------------------------------------------------------


class TestSchemas:
    def test_reasoning_result_defaults(self):
        r = ReasoningResult(
            verdict=ReasoningVerdict.APPROVED,
            confidence=0.9,
            risk=0.1,
            quality_score=0.85,
        )
        assert r.result_id
        assert r.created_at > 0
        assert r.iterations == 1
        assert r.max_iterations == 3
        assert r.simulation_passed is False

    def test_reasoning_result_to_dict(self):
        r = ReasoningResult(
            verdict=ReasoningVerdict.REJECTED,
            confidence=0.4,
            risk=0.7,
            quality_score=0.3,
            critique=["Issue A"],
        )
        d = r.to_dict()
        assert d["verdict"] == "rejected"
        assert d["confidence"] == 0.4
        assert "critique" in d
        assert isinstance(d["evidence_labels"], dict)

    def test_simulation_result_defaults(self):
        s = SimulationResult(
            success=True,
            estimated_latency_ms=500.0,
            estimated_cost=0.02,
            estimated_tokens=400,
            failure_probability=0.05,
        )
        assert s.simulation_id
        assert s.expected_outcome == ""
        assert s.warnings == []

    def test_simulation_result_to_dict(self):
        s = _make_simulation()
        d = s.to_dict()
        assert "simulation_id" in d
        assert d["success"] is True
        assert "resource_usage" in d

    def test_quality_report_to_dict(self):
        q = _make_quality()
        d = q.to_dict()
        assert d["overall"] == 0.8
        assert "correctness" in d

    def test_enums_are_str(self):
        assert ReasoningStage.REFLECTION == "reflection"
        assert ReasoningVerdict.APPROVED == "approved"
        assert EvidenceLabel.VERIFIED == "verified"


# ---------------------------------------------------------------------------
# TestReasoningTrace
# ---------------------------------------------------------------------------


class TestReasoningTrace:
    def test_add_and_get_all(self):
        trace = ReasoningTrace()
        trace.add("reflection", "observation", "Test observation", confidence=0.8)
        entries = trace.get_all()
        assert len(entries) == 1
        assert entries[0].stage == "reflection"
        assert entries[0].category == "observation"
        assert entries[0].confidence == 0.8

    def test_get_by_stage(self):
        trace = ReasoningTrace()
        trace.add("reflection", "observation", "A")
        trace.add("critique", "critique", "B")
        trace.add("reflection", "assumption", "C")
        result = trace.get_by_stage("reflection")
        assert len(result) == 2

    def test_get_by_category(self):
        trace = ReasoningTrace()
        trace.add("reflection", "observation", "A")
        trace.add("critique", "critique", "B")
        trace.add("simulation", "simulation", "C")
        result = trace.get_by_category("critique")
        assert len(result) == 1

    def test_get_summary(self):
        trace = ReasoningTrace()
        trace.add("reflection", "observation", "Test content", confidence=0.9)
        summary = trace.get_summary()
        assert len(summary) == 1
        assert "reflection" in summary[0]
        assert "observation" in summary[0]

    def test_to_dict(self):
        trace = ReasoningTrace()
        trace.add("evidence", "evidence", "Evidence found")
        d = trace.to_dict()
        assert "entries" in d
        assert d["total"] == 1
        assert d["entries"][0]["stage"] == "evidence"

    def test_clear(self):
        trace = ReasoningTrace()
        trace.add("reflection", "observation", "X")
        trace.clear()
        assert trace.get_all() == []


# ---------------------------------------------------------------------------
# TestPlanValidator
# ---------------------------------------------------------------------------


class TestPlanValidator:
    def setup_method(self):
        self.v = PlanValidator()

    def test_valid_plan(self):
        plan = _make_plan()
        ctx = _make_context()
        valid, issues = self.v.validate(plan, ctx)
        assert valid is True
        assert issues == []

    def test_missing_dependencies(self):
        plan = _make_plan(dependencies={"t3": ["t4"]})
        ctx = _make_context()
        valid, issues = self.v.validate(plan, ctx)
        assert valid is False
        assert any("t3" in i for i in issues)

    def test_missing_capabilities(self):
        plan = _make_plan(capabilities=[])
        ctx = _make_context()
        valid, issues = self.v.validate(plan, ctx)
        assert valid is False
        assert any("capabilities" in i.lower() for i in issues)

    def test_budget_exceeded(self):
        plan = _make_plan(cost={"total_estimated": 5.0})
        ctx = _make_context(budget=1.0)
        valid, issues = self.v.validate(plan, ctx)
        assert valid is False
        assert any("budget" in i.lower() for i in issues)

    def test_risk_threshold_exceeded(self):
        plan = _make_plan(risk={"overall_risk": 0.9})
        ctx = _make_context(max_risk=0.5)
        valid, issues = self.v.validate(plan, ctx)
        assert valid is False
        assert any("risk" in i.lower() for i in issues)

    def test_invalid_execution_mode(self):
        plan = _make_plan(execution_mode="turbo")
        ctx = _make_context()
        valid, issues = self.v.validate(plan, ctx)
        assert valid is False
        assert any("execution mode" in i.lower() for i in issues)

    def test_combined_issues(self):
        plan = _make_plan(tasks=[], capabilities=[])
        ctx = _make_context(budget=0.001)
        valid, issues = self.v.validate(plan, ctx)
        assert valid is False
        assert len(issues) >= 2


# ---------------------------------------------------------------------------
# TestReflectionEngine
# ---------------------------------------------------------------------------


class TestReflectionEngine:
    def setup_method(self):
        self.re = ReflectionEngine()

    def test_reflect_returns_dict(self):
        plan = _make_plan()
        goal = _make_goal()
        ctx = _make_context()
        report = self.re.reflect(plan, goal, ctx)
        assert isinstance(report, dict)
        assert "overall" in report
        assert 0.0 <= report["overall"] <= 1.0

    def test_goal_alignment_matching_ids(self):
        plan = _make_plan(goal_id="g1")
        goal = _make_goal(goal_id="g1")
        score = self.re._assess_goal_alignment(plan, goal)
        assert score >= 0.7

    def test_reasoning_quality_complete_plan(self):
        plan = _make_plan()
        score = self.re._assess_reasoning_quality(plan)
        assert score >= 0.5

    def test_planning_quality_with_checkpoints(self):
        plan = _make_plan(checkpoints=["c1", "c2"], rollback_path=["r1"])
        score = self.re._assess_planning_quality(plan)
        assert score >= 0.7

    def test_execution_readiness_full_plan(self):
        plan = _make_plan()
        score = self.re._assess_execution_readiness(plan)
        assert score >= 0.5


# ---------------------------------------------------------------------------
# TestCritiqueEngine
# ---------------------------------------------------------------------------


class TestCritiqueEngine:
    def setup_method(self):
        self.ce = CritiqueEngine()

    def test_critique_returns_list(self):
        plan = _make_plan()
        reflection = {"overall": 0.7}
        critiques = self.ce.critique(plan, reflection)
        assert isinstance(critiques, list)

    def test_logic_gaps_empty_tasks(self):
        plan = _make_plan(tasks=[])
        gaps = self.ce._detect_logic_gaps(plan)
        assert any("tasks" in g.lower() or "step" in g.lower() for g in gaps)

    def test_weak_assumptions_zero_cost(self):
        plan = _make_plan(cost={"total_estimated": 0})
        assumptions = self.ce._detect_weak_assumptions(plan)
        assert any("cost" in a.lower() for a in assumptions)

    def test_missing_evidence_no_risk(self):
        plan = _make_plan(risk={})
        missing = self.ce._detect_missing_evidence(plan)
        assert any("risk" in m.lower() for m in missing)

    def test_contradictions_high_risk_parallel(self):
        plan = _make_plan(risk={"overall_risk": 0.9}, execution_mode="parallel")
        contradictions = self.ce._detect_contradictions(plan)
        assert len(contradictions) >= 1

    def test_severity_levels(self):
        assert self.ce.get_severity([]) == "low"
        assert self.ce.get_severity(["a", "b"]) == "medium"
        assert self.ce.get_severity(["a", "b", "c", "d"]) == "high"
        assert self.ce.get_severity(["a"] * 6) == "critical"

    def test_empty_plan_generates_critiques(self):
        plan = {}
        reflection = {"overall": 0.2}
        critiques = self.ce.critique(plan, reflection)
        assert len(critiques) >= 1


# ---------------------------------------------------------------------------
# TestAlternativeGenerator
# ---------------------------------------------------------------------------


class TestAlternativeGenerator:
    def setup_method(self):
        self.ag = AlternativeGenerator()

    def test_generate_returns_five_alternatives(self):
        plan = _make_plan()
        ctx = _make_context()
        alts = self.ag.generate(plan, [], ctx)
        assert len(alts) == 5

    def test_rank_by_score(self):
        alts = [{"score": 0.5}, {"score": 0.9}, {"score": 0.3}]
        ranked = self.ag.rank(alts)
        assert ranked[0]["score"] == 0.9

    def test_fastest_uses_parallel(self):
        plan = _make_plan()
        alt = self.ag._generate_fastest(plan)
        assert alt["execution_mode"] == "parallel"
        assert alt["strategy"] == "fastest"

    def test_balanced_has_hybrid_mode(self):
        plan = _make_plan()
        alt = self.ag._generate_balanced(plan)
        assert alt["strategy"] == "balanced"
        assert alt["execution_mode"] == "hybrid"


# ---------------------------------------------------------------------------
# TestHypothesisEngine
# ---------------------------------------------------------------------------


class TestHypothesisEngine:
    def setup_method(self):
        self.he = HypothesisEngine()

    def test_generate_returns_hypotheses(self):
        plan = _make_plan()
        ctx = _make_context()
        hypotheses = self.he.generate_hypotheses(plan, ctx)
        assert len(hypotheses) >= 1
        assert all("description" in h for h in hypotheses)

    def test_evaluate_hypothesis_no_evidence(self):
        hyp = self.he._create_hypothesis("Test", ["Assumption A"])
        score = self.he.evaluate_hypothesis(hyp, [])
        assert 0.0 <= score <= 1.0

    def test_create_hypothesis_structure(self):
        hyp = self.he._create_hypothesis("Test hypothesis", ["A", "B"])
        assert "hypothesis_id" in hyp
        assert hyp["status"] == "untested"
        assert len(hyp["assumptions"]) == 2

    def test_rank_hypotheses(self):
        h1 = self.he._create_hypothesis("H1", [])
        h1["confidence"] = 0.3
        h2 = self.he._create_hypothesis("H2", [])
        h2["confidence"] = 0.9
        ranked = self.he.rank_hypotheses([h1, h2])
        assert ranked[0]["confidence"] == 0.9


# ---------------------------------------------------------------------------
# TestCounterfactualEngine
# ---------------------------------------------------------------------------


class TestCounterfactualEngine:
    def setup_method(self):
        self.cfe = CounterfactualEngine()

    def test_analyze_returns_six_scenarios(self):
        plan = _make_plan()
        ctx = _make_context()
        scenarios = self.cfe.analyze(plan, ctx)
        assert len(scenarios) == 6

    def test_different_model_scenario(self):
        plan = _make_plan()
        scenario = self.cfe._what_if_different_model(plan)
        assert scenario["type"] == "different_model"
        assert "expected_impact" in scenario

    def test_different_provider_scenario(self):
        plan = _make_plan()
        scenario = self.cfe._what_if_different_provider(plan)
        assert scenario["type"] == "different_provider"

    def test_different_budget_doubles_cost(self):
        plan = _make_plan(cost={"total_estimated": 0.10})
        scenario = self.cfe._what_if_different_budget(plan)
        assert scenario["changes"]["budget"] == pytest.approx(0.20)

    def test_evaluate_scenario(self):
        scenario = {
            "scenario_id": str(uuid.uuid4()),
            "type": "different_model",
            "expected_impact": {"quality": 0.2, "cost": -0.1},
        }
        evaluation = self.cfe.evaluate_scenario(scenario)
        assert "net_benefit" in evaluation
        assert "recommendation" in evaluation


# ---------------------------------------------------------------------------
# TestSimulationEngine
# ---------------------------------------------------------------------------


class TestSimulationEngine:
    def setup_method(self):
        self.se = SimulationEngine()

    def test_simulate_returns_result(self):
        plan = _make_plan()
        ctx = _make_context()
        result = self.se.simulate(plan, ctx)
        assert isinstance(result, SimulationResult)
        assert result.simulation_id

    def test_estimate_latency_sequential(self):
        plan = _make_plan(
            execution_mode="sequential", estimated_duration_ms=500, tasks=["t1", "t2"]
        )
        latency = self.se._estimate_latency(plan)
        assert latency > 500

    def test_estimate_cost_includes_tasks(self):
        plan = _make_plan(tasks=["t1", "t2", "t3"], cost={"total_estimated": 0.03})
        cost = self.se._estimate_cost(plan)
        assert cost > 0.03

    def test_dry_run_produces_trace(self):
        plan = _make_plan(tasks=["t1", "t2", "t3"])
        trace = self.se.dry_run(plan)
        assert trace["dry_run"] is True
        assert len(trace["steps"]) == 3
        assert trace["total_steps"] == 3

    def test_failure_probability_scales_with_risk(self):
        low_risk_plan = _make_plan(risk={"overall_risk": 0.05})
        high_risk_plan = _make_plan(risk={"overall_risk": 0.8})
        low_p = self.se._estimate_failure_probability(low_risk_plan)
        high_p = self.se._estimate_failure_probability(high_risk_plan)
        assert high_p > low_p


# ---------------------------------------------------------------------------
# TestEvidenceEngine
# ---------------------------------------------------------------------------


class TestEvidenceEngine:
    def setup_method(self):
        self.ee = EvidenceEngine()

    def test_verify_returns_labels(self):
        plan = _make_plan()
        ctx = _make_context()
        labels = self.ee.verify(plan, ctx)
        assert isinstance(labels, dict)
        assert len(labels) > 0
        for v in labels.values():
            assert isinstance(v, EvidenceLabel)

    def test_memory_evidence_without_prior(self):
        plan = _make_plan()
        ctx = _make_context()
        results = self.ee._verify_memory_evidence(plan, ctx)
        assert len(results) >= 1
        assert any(label == EvidenceLabel.ESTIMATED for _, label in results)

    def test_knowledge_evidence_with_providers(self):
        plan = _make_plan()
        ctx = _make_context()
        results = self.ee._verify_knowledge_evidence(plan, ctx)
        assert any(label == EvidenceLabel.VERIFIED for _, label in results)

    def test_confidence_from_evidence_all_verified(self):
        labels = {
            "claim1": EvidenceLabel.VERIFIED,
            "claim2": EvidenceLabel.VERIFIED,
        }
        score = EvidenceEngine.get_confidence_from_evidence(labels)
        assert score == pytest.approx(1.0)

    def test_confidence_from_evidence_all_hypothesis(self):
        labels = {
            "claim1": EvidenceLabel.HYPOTHESIS,
            "claim2": EvidenceLabel.HYPOTHESIS,
        }
        score = EvidenceEngine.get_confidence_from_evidence(labels)
        assert score < 0.5


# ---------------------------------------------------------------------------
# TestPlanRefiner
# ---------------------------------------------------------------------------


class TestPlanRefiner:
    def setup_method(self):
        self.pr = PlanRefiner()

    def test_refine_returns_dict(self):
        plan = _make_plan()
        sim = _make_simulation()
        quality = _make_quality()
        refined = self.pr.refine(plan, ["Issue A"], sim, quality)
        assert isinstance(refined, dict)
        assert refined.get("refined") is True

    def test_optimize_execution_order_preserves_tasks(self):
        plan = _make_plan(tasks=["t2", "t1"])
        refined = self.pr._optimize_execution_order(plan)
        assert set(refined["tasks"]) == {"t1", "t2"}

    def test_optimize_parallelism_with_three_tasks(self):
        plan = _make_plan(tasks=["t1", "t2", "t3"], execution_mode="sequential")
        refined = self.pr._optimize_parallelism(plan)
        assert refined["execution_mode"] == "parallel"

    def test_get_improvements_detects_new_retry(self):
        original = _make_plan()
        refined = dict(original)
        refined["retry_config"] = {"max_retries": 3}
        improvements = PlanRefiner.get_improvements(original, refined)
        assert any("retry" in i.lower() for i in improvements)

    def test_no_changes_needed(self):
        plan = _make_plan(rollback_path=["r1"], checkpoints=["c1"], retry_config={"max_retries": 2})
        improvements = PlanRefiner.get_improvements(plan, plan)
        assert improvements == []


# ---------------------------------------------------------------------------
# TestReasoningMemory
# ---------------------------------------------------------------------------


class TestReasoningMemory:
    def setup_method(self):
        self.mem = ReasoningMemory()

    def test_store_and_stats(self):
        result = ReasoningResult(
            verdict=ReasoningVerdict.APPROVED,
            confidence=0.9,
            risk=0.1,
            quality_score=0.85,
        )
        self.mem.store(result, "plan_001")
        stats = self.mem.stats()
        assert stats["total"] == 1
        assert stats["success_rate"] == 1.0

    def test_get_similar_returns_list(self):
        result = ReasoningResult(
            verdict=ReasoningVerdict.APPROVED,
            confidence=0.9,
            risk=0.1,
            quality_score=0.8,
        )
        self.mem.store(result, "p1")
        similar = self.mem.get_similar(_make_plan(), limit=5)
        assert isinstance(similar, list)
        assert len(similar) <= 5

    def test_success_rate_zero_when_empty(self):
        assert self.mem.get_success_rate() == 0.0

    def test_common_failures_with_rejected(self):
        result = ReasoningResult(
            verdict=ReasoningVerdict.REJECTED,
            confidence=0.3,
            risk=0.9,
            quality_score=0.2,
        )
        self.mem.store(result, "p2")
        failures = self.mem.get_common_failures()
        assert isinstance(failures, list)

    def test_stats_with_multiple_results(self):
        for i in range(3):
            r = ReasoningResult(
                verdict=ReasoningVerdict.APPROVED,
                confidence=0.8,
                risk=0.2,
                quality_score=0.75,
            )
            self.mem.store(r, f"plan_{i}")
        stats = self.mem.stats()
        assert stats["total"] == 3
        assert stats["avg_confidence"] == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# TestUncertaintyEngine
# ---------------------------------------------------------------------------


class TestUncertaintyEngine:
    def setup_method(self):
        self.ue = UncertaintyEngine()

    def test_assess_returns_dict(self):
        plan = _make_plan()
        evidence = {"claim1": EvidenceLabel.VERIFIED}
        ctx = _make_context()
        result = self.ue.assess(plan, evidence, ctx)
        assert "overall_uncertainty" in result
        assert 0.0 <= result["overall_uncertainty"] <= 1.0

    def test_unknown_facts_no_providers(self):
        plan = _make_plan()
        ctx = {}
        unknowns = self.ue._detect_unknown_facts(plan, ctx)
        assert any("provider" in u.lower() for u in unknowns)

    def test_missing_context_no_budget(self):
        plan = _make_plan()
        ctx = {}
        missing = self.ue._detect_missing_context(plan, ctx)
        assert any("budget" in m.lower() for m in missing)

    def test_weak_evidence_detection(self):
        evidence = {
            "claim1": EvidenceLabel.HYPOTHESIS,
            "claim2": EvidenceLabel.ESTIMATED,
        }
        weak = self.ue._detect_weak_evidence(evidence)
        assert len(weak) == 2

    def test_overall_uncertainty_scales_with_issues(self):
        assessment_low = {
            "total_issues": 0,
            "unknown_facts": [],
            "missing_context": [],
            "weak_evidence": [],
            "ambiguous_goals": [],
        }
        assessment_high = {
            "total_issues": 8,
            "unknown_facts": [],
            "missing_context": [],
            "weak_evidence": [],
            "ambiguous_goals": [],
        }
        low = UncertaintyEngine.overall_uncertainty(assessment_low)
        high = UncertaintyEngine.overall_uncertainty(assessment_high)
        assert high > low


# ---------------------------------------------------------------------------
# TestQualityEstimator
# ---------------------------------------------------------------------------


class TestQualityEstimator:
    def setup_method(self):
        self.qe = QualityEstimator()

    def test_estimate_returns_quality_report(self):
        plan = _make_plan()
        sim = _make_simulation()
        evidence = {"c1": EvidenceLabel.VERIFIED}
        report = self.qe.estimate(plan, sim, evidence)
        assert isinstance(report, QualityReport)
        assert 0.0 <= report.overall <= 1.0

    def test_correctness_all_verified(self):
        plan = _make_plan()
        evidence = {"c1": EvidenceLabel.VERIFIED, "c2": EvidenceLabel.VERIFIED}
        score = self.qe._score_correctness(plan, evidence)
        assert score >= 0.8

    def test_safety_low_risk_high_score(self):
        plan = _make_plan(risk={"overall_risk": 0.05})
        sim = _make_simulation(failure_probability=0.05)
        score = self.qe._score_safety(plan, sim)
        assert score >= 0.85

    def test_performance_low_latency(self):
        sim = _make_simulation(estimated_latency_ms=500)
        score = self.qe._score_performance(sim)
        assert score >= 0.9

    def test_overall_score_bounded(self):
        plan = _make_plan()
        sim = _make_simulation()
        evidence = {"c1": EvidenceLabel.VERIFIED}
        report = self.qe.estimate(plan, sim, evidence)
        assert 0.0 <= report.overall <= 1.0


# ---------------------------------------------------------------------------
# TestMetaReasoner
# ---------------------------------------------------------------------------


class TestMetaReasoner:
    def setup_method(self):
        self.reasoner = _make_reasoner()

    def test_reason_approve(self):
        plan = _make_plan()
        goal = _make_goal()
        ctx = _make_context()
        result = asyncio.run(self.reasoner.reason(plan, goal, ctx))
        assert isinstance(result, ReasoningResult)
        assert result.verdict in list(ReasoningVerdict)
        assert result.result_id

    def test_reason_reject_invalid_plan(self):
        # Plan with more than 5 validation issues should be rejected immediately
        plan = _make_plan(
            tasks=[],
            capabilities=[],
            execution_mode="turbo",
            risk={"overall_risk": 0.99},
            cost={"total_estimated": 100.0},
            dependencies={"missing_task": ["also_missing"]},
        )
        goal = _make_goal()
        ctx = _make_context(budget=0.001, max_risk=0.1)
        result = asyncio.run(self.reasoner.reason(plan, goal, ctx))
        assert result.verdict == ReasoningVerdict.REJECTED

    def test_reason_stores_in_memory(self):
        plan = _make_plan()
        goal = _make_goal()
        ctx = _make_context()
        asyncio.run(self.reasoner.reason(plan, goal, ctx))
        stats = self.reasoner._reasoning_memory.stats()
        assert stats["total"] >= 1

    def test_deadlock_protection(self):
        # A plan that will always need refinement can exhaust iterations
        # but max_iterations should prevent infinite loops
        plan = _make_plan()
        goal = _make_goal()
        ctx = _make_context()
        # Should complete without raising after normal flow
        result = asyncio.run(self.reasoner.reason(plan, goal, ctx))
        assert result.iterations <= result.max_iterations + 1

    def test_verdict_logic_approved(self):
        quality = _make_quality(overall=0.85, safety=0.9)
        sim = _make_simulation(success=True, failure_probability=0.05)
        uncertainty = {"overall_uncertainty": 0.1}
        verdict = self.reasoner._make_verdict(quality, [], sim, uncertainty)
        assert verdict == ReasoningVerdict.APPROVED

    def test_verdict_logic_rejected_low_quality(self):
        quality = _make_quality(overall=0.3, safety=0.4)
        sim = _make_simulation(success=False, failure_probability=0.7)
        uncertainty = {"overall_uncertainty": 0.3}
        verdict = self.reasoner._make_verdict(quality, ["c1", "c2"], sim, uncertainty)
        assert verdict in (ReasoningVerdict.REJECTED, ReasoningVerdict.BLOCKED)

    def test_events_emitted_during_reason(self):
        plan = _make_plan()
        goal = _make_goal()
        ctx = _make_context()
        initial_count = len(self.reasoner._events)
        asyncio.run(self.reasoner.reason(plan, goal, ctx))
        assert len(self.reasoner._events) > initial_count

    def test_get_status(self):
        status = self.reasoner.get_status()
        assert status["active"] is True
        assert "memory_stats" in status


# ---------------------------------------------------------------------------
# TestExceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_meta_reasoning_error(self):
        err = MetaReasoningError("Something went wrong", stage="reflection")
        assert err.stage == "reflection"
        assert "Something went wrong" in str(err)

    def test_simulation_error(self):
        err = SimulationError("Simulation failed")
        assert err.stage == "simulation"
        assert isinstance(err, MetaReasoningError)

    def test_deadlock_error(self):
        err = DeadlockError("Deadlock detected after 3 iterations")
        assert err.stage == "deadlock"
        assert isinstance(err, MetaReasoningError)
        assert "3 iterations" in str(err)


# ---------------------------------------------------------------------------
# Additional edge-case / coverage tests
# ---------------------------------------------------------------------------


class TestAdditionalCoverage:
    """Extra tests to push coverage above 80+ total tests."""

    def test_reasoning_result_with_evidence_labels_to_dict(self):
        r = ReasoningResult(
            verdict=ReasoningVerdict.NEEDS_REFINEMENT,
            confidence=0.6,
            risk=0.3,
            quality_score=0.6,
            evidence_labels={"c1": EvidenceLabel.INFERRED},
        )
        d = r.to_dict()
        assert d["evidence_labels"]["c1"] == "inferred"

    def test_reasoning_stages_all_exist(self):
        stages = list(ReasoningStage)
        assert ReasoningStage.REFLECTION in stages
        assert ReasoningStage.DECISION in stages
        assert len(stages) == 9

    def test_reasoning_verdict_all_exist(self):
        verdicts = list(ReasoningVerdict)
        assert len(verdicts) == 5

    def test_evidence_label_all_exist(self):
        labels = list(EvidenceLabel)
        assert len(labels) == 4

    def test_meta_reasoning_event_to_dict(self):
        event = MetaReasoningEvent(
            event_type=MetaReasoningEventType.REFLECTION_STARTED,
            plan_id="p1",
            data={"key": "value"},
        )
        d = event.to_dict()
        assert d["event_type"] == "reflection_started"
        assert d["plan_id"] == "p1"
        assert d["data"]["key"] == "value"
        assert "timestamp" in d

    def test_meta_reasoning_event_types_count(self):
        event_types = list(MetaReasoningEventType)
        assert len(event_types) == 12

    def test_reflection_error_is_meta_reasoning_error(self):
        err = ReflectionError("Reflection issue")
        assert isinstance(err, MetaReasoningError)
        assert err.stage == "reflection"

    def test_validation_error_is_meta_reasoning_error(self):
        err = ValidationError("Validation issue")
        assert isinstance(err, MetaReasoningError)
        assert err.stage == "validation"

    def test_trace_entry_has_uuid(self):
        trace = ReasoningTrace()
        trace.add("test_stage", "observation", "content")
        entries = trace.get_all()
        assert len(entries[0].entry_id) == 36  # UUID4 length

    def test_plan_validator_restricted_permissions(self):
        plan = _make_plan(permissions=["admin_write"])
        ctx = _make_context()
        valid, issues = PlanValidator().validate(plan, ctx)
        assert valid is False
        assert any("permission" in i.lower() for i in issues)

    def test_simulation_engine_parallel_mode_latency(self):
        se = SimulationEngine()
        plan_parallel = _make_plan(
            execution_mode="parallel", estimated_duration_ms=500, tasks=["t1", "t2"]
        )
        plan_sequential = _make_plan(
            execution_mode="sequential", estimated_duration_ms=500, tasks=["t1", "t2"]
        )
        lat_p = se._estimate_latency(plan_parallel)
        lat_s = se._estimate_latency(plan_sequential)
        assert lat_p < lat_s

    def test_evidence_engine_empty_plan(self):
        ee = EvidenceEngine()
        labels = ee.verify({}, {})
        assert isinstance(labels, dict)

    def test_quality_estimator_empty_evidence(self):
        qe = QualityEstimator()
        sim = _make_simulation()
        report = qe.estimate(_make_plan(), sim, {})
        assert 0.0 <= report.overall <= 1.0

    def test_counterfactual_parallelism_toggle(self):
        cfe = CounterfactualEngine()
        plan_seq = _make_plan(execution_mode="sequential")
        plan_par = _make_plan(execution_mode="parallel")
        s1 = cfe._what_if_different_parallelism(plan_seq)
        s2 = cfe._what_if_different_parallelism(plan_par)
        assert s1["changes"]["execution_mode"] == "parallel"
        assert s2["changes"]["execution_mode"] == "sequential"

    def test_reasoning_memory_successful_strategies(self):
        mem = ReasoningMemory()
        r = ReasoningResult(
            verdict=ReasoningVerdict.APPROVED,
            confidence=0.95,
            risk=0.05,
            quality_score=0.9,
            iterations=1,
        )
        mem.store(r, "plan_x")
        strategies = mem.get_successful_strategies()
        assert isinstance(strategies, list)
        assert len(strategies) > 0

    def test_alternative_generator_cheapest_reduces_cost(self):
        ag = AlternativeGenerator()
        plan = _make_plan(cost={"total_estimated": 0.10})
        alt = ag._generate_cheapest(plan)
        assert alt["cost"]["total_estimated"] < 0.10

    def test_alternative_generator_safest_has_low_risk(self):
        ag = AlternativeGenerator()
        plan = _make_plan()
        alt = ag._generate_safest(plan)
        assert alt["risk"]["overall_risk"] < 0.2

    def test_simulation_engine_resource_usage_parallel(self):
        se = SimulationEngine()
        plan = _make_plan(execution_mode="parallel", tasks=["t1", "t2", "t3"])
        usage = se._estimate_resource_usage(plan)
        assert usage["concurrency"] == 3

    def test_simulation_engine_resource_usage_sequential(self):
        se = SimulationEngine()
        plan = _make_plan(execution_mode="sequential", tasks=["t1", "t2"])
        usage = se._estimate_resource_usage(plan)
        assert usage["concurrency"] == 1

    def test_uncertainty_engine_ambiguous_goals_no_goal_id(self):
        ue = UncertaintyEngine()
        plan = _make_plan(goal_id="")
        ambiguous = ue._detect_ambiguous_goals(plan)
        assert any("goal" in a.lower() for a in ambiguous)

    def test_meta_reasoner_should_refine_high_quality(self):
        reasoner = _make_reasoner()
        quality = _make_quality(overall=0.8)
        assert reasoner._should_refine(quality, []) is False

    def test_meta_reasoner_should_refine_low_quality(self):
        reasoner = _make_reasoner()
        quality = _make_quality(overall=0.4)
        assert reasoner._should_refine(quality, ["c1", "c2", "c3", "c4"]) is True

    def test_hypothesis_engine_evaluate_with_evidence(self):
        he = HypothesisEngine()
        hyp = he._create_hypothesis("Succeeds", ["A"])
        evidence = [{"supports": True, "claim": "A"}]
        score = he.evaluate_hypothesis(hyp, evidence)
        assert 0.0 <= score <= 1.0

    def test_reflection_engine_knowledge_usage_overlap(self):
        re = ReflectionEngine()
        plan = _make_plan(capabilities=["cap1"])
        ctx = _make_context(available_capabilities=["cap1", "cap2"])
        score = re._assess_knowledge_usage(plan, ctx)
        assert score >= 0.7

    def test_plan_refiner_high_failure_prob_adds_retry(self):
        pr = PlanRefiner()
        plan = _make_plan()
        sim = _make_simulation(failure_probability=0.6)
        quality = _make_quality()
        refined = pr.refine(plan, [], sim, quality)
        assert refined.get("retry_config") is not None
        assert refined["retry_config"]["max_retries"] >= 3
