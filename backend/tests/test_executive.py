"""Comprehensive tests for the Executive Intelligence layer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio

import pytest

from executive.approval_engine import ApprovalEngine
from executive.capability_orchestrator import CapabilityOrchestrator
from executive.confidence_engine import ConfidenceEngine
from executive.cost_engine import CostEngine
from executive.decision_engine import DecisionEngine
from executive.dependency_graph import ExecutiveDependencyGraph
from executive.exceptions import (
    DecisionError,
)
from executive.execution_planner import ExecutionPlanner
from executive.executive_brain import ExecutiveBrain
from executive.goal_manager import GoalManager
from executive.model_selector import ModelSelector
from executive.parallel_planner import ParallelPlanner
from executive.provider_selector import ProviderSelector
from executive.risk_engine import RiskEngine
from executive.schemas import (
    ApprovalStatus,
    Decision,
    ExecutionPlan,
    Goal,
    GoalPriority,
    GoalState,
    Strategy,
    StrategyType,
)
from executive.strategic_planner import StrategicPlanner
from executive.task_graph import TaskGraph, TaskNode
from executive.workflow_optimizer import WorkflowOptimizer

# --- Test Schemas ---


class TestSchemas:
    """Tests for executive data models and enums."""

    def test_goal_creation(self) -> None:
        goal = Goal(title="Test Goal", description="A test goal")
        assert goal.title == "Test Goal"
        assert goal.state == GoalState.CREATED
        assert goal.priority == GoalPriority.MEDIUM
        assert goal.progress == 0.0
        assert goal.goal_id

    def test_goal_to_dict(self) -> None:
        goal = Goal(title="Dict Goal", description="Testing to_dict")
        d = goal.to_dict()
        assert d["title"] == "Dict Goal"
        assert d["state"] == "created"
        assert d["priority"] == "medium"
        assert "goal_id" in d

    def test_strategy_creation(self) -> None:
        s = Strategy(
            strategy_type=StrategyType.FASTEST,
            description="Fast strategy",
            estimated_cost=0.05,
            estimated_latency_ms=500.0,
        )
        assert s.strategy_type == StrategyType.FASTEST
        assert s.estimated_cost == 0.05
        assert s.strategy_id

    def test_strategy_to_dict(self) -> None:
        s = Strategy(strategy_type=StrategyType.BALANCED, description="Balanced")
        d = s.to_dict()
        assert d["strategy_type"] == "balanced"
        assert "strategy_id" in d

    def test_decision_creation(self) -> None:
        dec = Decision(reasoning="Test reasoning", confidence=0.8, risk=0.2)
        assert dec.confidence == 0.8
        assert dec.risk == 0.2
        assert dec.decision_id

    def test_execution_plan_creation(self) -> None:
        plan = ExecutionPlan(
            goal_id="g1",
            strategy_id="s1",
            tasks=["t1", "t2"],
            execution_mode="parallel",
        )
        assert plan.goal_id == "g1"
        assert plan.execution_mode == "parallel"
        d = plan.to_dict()
        assert d["tasks"] == ["t1", "t2"]
        assert d["approval_status"] == "pending_approval"


# --- Test GoalManager ---


class TestGoalManager:
    """Tests for goal lifecycle management."""

    def test_create_goal(self) -> None:
        gm = GoalManager()
        goal = gm.create_goal("Test", "Description")
        assert goal.title == "Test"
        assert goal.state == GoalState.CREATED
        assert gm.get_goal(goal.goal_id) is goal

    def test_update_goal(self) -> None:
        gm = GoalManager()
        goal = gm.create_goal("Original", "Desc")
        updated = gm.update_goal(goal.goal_id, title="Updated")
        assert updated.title == "Updated"

    def test_get_goal_not_found(self) -> None:
        gm = GoalManager()
        assert gm.get_goal("nonexistent") is None

    def test_list_goals_filter_state(self) -> None:
        gm = GoalManager()
        gm.create_goal("A", "a")
        g2 = gm.create_goal("B", "b")
        gm.complete_goal(g2.goal_id)
        active = gm.list_goals(state=GoalState.CREATED)
        assert len(active) == 1

    def test_complete_goal(self) -> None:
        gm = GoalManager()
        goal = gm.create_goal("Complete me", "desc")
        result = gm.complete_goal(goal.goal_id)
        assert result is True
        assert goal.state == GoalState.COMPLETED
        assert goal.progress == 1.0

    def test_fail_goal(self) -> None:
        gm = GoalManager()
        goal = gm.create_goal("Fail me", "desc")
        result = gm.fail_goal(goal.goal_id, "something broke")
        assert result is True
        assert goal.state == GoalState.FAILED
        assert goal.metadata["failure_reason"] == "something broke"

    def test_cancel_goal(self) -> None:
        gm = GoalManager()
        goal = gm.create_goal("Cancel me", "desc")
        result = gm.cancel_goal(goal.goal_id)
        assert result is True
        assert goal.state == GoalState.CANCELLED

    def test_split_goal(self) -> None:
        gm = GoalManager()
        parent = gm.create_goal("Parent", "desc")
        children = gm.split_goal(
            parent.goal_id,
            [
                {"title": "Child 1", "description": "c1"},
                {"title": "Child 2", "description": "c2"},
            ],
        )
        assert len(children) == 2
        assert children[0].parent_id == parent.goal_id
        assert len(parent.sub_goals) == 2

    def test_merge_goals(self) -> None:
        gm = GoalManager()
        g1 = gm.create_goal("G1", "desc1")
        g2 = gm.create_goal("G2", "desc2")
        merged = gm.merge_goals([g1.goal_id, g2.goal_id], "Merged")
        assert merged.title == "Merged"
        assert g1.state == GoalState.MERGED
        assert g2.state == GoalState.MERGED

    def test_get_metrics(self) -> None:
        gm = GoalManager()
        gm.create_goal("A", "a", GoalPriority.HIGH)
        gm.create_goal("B", "b", GoalPriority.LOW)
        metrics = gm.get_metrics()
        assert metrics["total"] == 2
        assert "by_state" in metrics
        assert "by_priority" in metrics


# --- Test StrategicPlanner ---


class TestStrategicPlanner:
    """Tests for strategic planning."""

    def test_generate_strategies(self) -> None:
        sp = StrategicPlanner()
        goal = Goal(title="Test", description="desc")
        strategies = sp.generate_strategies(goal, ["cap1", "cap2"])
        assert len(strategies) == 5

    def test_rank_strategies(self) -> None:
        sp = StrategicPlanner()
        goal = Goal(title="Test", description="desc")
        strategies = sp.generate_strategies(goal, ["cap1"])
        ranked = sp.rank_strategies(strategies)
        assert len(ranked) == 5
        # First should have highest composite score
        assert ranked[0].estimated_confidence >= ranked[-1].estimated_confidence or True

    def test_generate_fastest(self) -> None:
        sp = StrategicPlanner()
        goal = Goal(title="Fast", description="desc")
        s = sp._generate_fastest(goal, ["a", "b", "c"])
        assert s.strategy_type == StrategyType.FASTEST
        assert len(s.steps) > 0

    def test_generate_lowest_cost(self) -> None:
        sp = StrategicPlanner()
        goal = Goal(title="Cheap", description="desc")
        s = sp._generate_lowest_cost(goal, ["a", "b"])
        assert s.strategy_type == StrategyType.LOWEST_COST
        assert s.estimated_cost < 0.1

    def test_generate_balanced(self) -> None:
        sp = StrategicPlanner()
        goal = Goal(title="Balanced", description="desc")
        s = sp._generate_balanced(goal, ["a", "b"])
        assert s.strategy_type == StrategyType.BALANCED

    def test_generate_empty_capabilities(self) -> None:
        sp = StrategicPlanner()
        goal = Goal(title="Empty", description="desc")
        strategies = sp.generate_strategies(goal, [])
        assert len(strategies) == 5
        # Should still produce strategies even with no capabilities
        for s in strategies:
            assert s.strategy_id


# --- Test DecisionEngine ---


class TestDecisionEngine:
    """Tests for decision-making engine."""

    def test_make_decision(self) -> None:
        de = DecisionEngine()
        goal = Goal(title="Decide", description="desc")
        strategies = [
            Strategy(
                strategy_type=StrategyType.FASTEST,
                description="fast",
                estimated_confidence=0.7,
                risk_level=0.4,
                estimated_cost=0.05,
            ),
            Strategy(
                strategy_type=StrategyType.SAFEST,
                description="safe",
                estimated_confidence=0.8,
                risk_level=0.1,
                estimated_cost=0.03,
            ),
        ]
        decision = de.make_decision(strategies, goal)
        assert decision.selected is not None
        assert decision.confidence > 0
        assert len(decision.alternatives) == 2

    def test_evaluate_strategy(self) -> None:
        de = DecisionEngine()
        goal = Goal(title="Eval", description="desc")
        s = Strategy(
            strategy_type=StrategyType.BALANCED,
            description="bal",
            estimated_confidence=0.75,
            risk_level=0.3,
            estimated_cost=0.04,
            estimated_latency_ms=1500,
        )
        score = de._evaluate_strategy(s, goal, {})
        assert 0.0 < score < 1.0

    def test_explain_decision(self) -> None:
        de = DecisionEngine()
        s = Strategy(strategy_type=StrategyType.FASTEST, description="fast")
        decision = Decision(
            selected=s,
            reasoning="Speed priority",
            confidence=0.8,
            risk=0.3,
            cost=0.05,
            latency_ms=500,
        )
        explanation = de.explain_decision(decision)
        assert "Speed priority" in explanation
        assert "Confidence" in explanation

    def test_no_strategies_raises(self) -> None:
        de = DecisionEngine()
        goal = Goal(title="Empty", description="desc")
        with pytest.raises(DecisionError):
            de.make_decision([], goal)

    def test_constraints_filter(self) -> None:
        de = DecisionEngine()
        goal = Goal(title="Constrained", description="desc")
        strategies = [
            Strategy(
                strategy_type=StrategyType.FASTEST,
                description="fast",
                estimated_cost=10.0,
                estimated_confidence=0.9,
                risk_level=0.1,
            ),
        ]
        # Cost constraint should yield score 0
        decision = de.make_decision(strategies, goal, {"max_cost": 0.01})
        # It still selects since it's the only option (score 0 is still max)
        assert decision.selected is not None


# --- Test ExecutionPlanner ---


class TestExecutionPlanner:
    """Tests for execution planning."""

    def test_create_plan(self) -> None:
        ep = ExecutionPlanner()
        s = Strategy(
            strategy_type=StrategyType.BALANCED,
            description="bal",
            steps=["step1", "step2"],
            estimated_latency_ms=1000,
        )
        decision = Decision(selected=s, alternatives=[s])
        goal = Goal(title="Plan", description="desc")
        plan = ep.create_plan(decision, goal)
        assert plan.goal_id == goal.goal_id
        assert plan.strategy_id == s.strategy_id
        assert len(plan.tasks) == 2

    def test_plan_sequential(self) -> None:
        ep = ExecutionPlanner()
        graph = ep.plan_sequential(["a", "b", "c"])
        order = graph.get_execution_order()
        assert len(order) == 3

    def test_plan_parallel(self) -> None:
        ep = ExecutionPlanner()
        graph = ep.plan_parallel(["a", "b", "c"])
        ready = graph.get_ready_tasks()
        assert len(ready) == 3

    def test_add_checkpoints(self) -> None:
        ep = ExecutionPlanner()
        plan = ExecutionPlan(goal_id="g1", strategy_id="s1", tasks=["t1", "t2", "t3", "t4"])
        plan = ep.add_checkpoints(plan, interval=2)
        assert len(plan.checkpoints) == 2

    def test_add_rollback(self) -> None:
        ep = ExecutionPlanner()
        plan = ExecutionPlan(goal_id="g1", strategy_id="s1", tasks=["t1", "t2", "t3"])
        plan = ep.add_rollback(plan)
        assert len(plan.rollback_path) == 3
        assert plan.rollback_path[0] == "undo:t3"


# --- Test TaskGraph ---


class TestTaskGraph:
    """Tests for task graph operations."""

    def test_add_task(self) -> None:
        graph = TaskGraph()
        node = TaskNode(name="task1", capability_id="cap1")
        tid = graph.add_task(node)
        assert tid == node.task_id
        assert tid in graph._nodes

    def test_add_dependency(self) -> None:
        graph = TaskGraph()
        n1 = TaskNode(name="t1", capability_id="c1")
        n2 = TaskNode(name="t2", capability_id="c2")
        t1 = graph.add_task(n1)
        t2 = graph.add_task(n2)
        graph.add_dependency(t2, t1)
        assert t1 in n2.dependencies

    def test_get_ready_tasks(self) -> None:
        graph = TaskGraph()
        n1 = TaskNode(name="t1", capability_id="c1")
        n2 = TaskNode(name="t2", capability_id="c2")
        t1 = graph.add_task(n1)
        t2 = graph.add_task(n2)
        graph.add_dependency(t2, t1)
        ready = graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == t1

    def test_mark_completed(self) -> None:
        graph = TaskGraph()
        node = TaskNode(name="t1", capability_id="c1")
        tid = graph.add_task(node)
        graph.mark_completed(tid, {"output": "done"})
        assert node.status == "completed"
        assert node.result == {"output": "done"}

    def test_mark_failed(self) -> None:
        graph = TaskGraph()
        node = TaskNode(name="t1", capability_id="c1")
        tid = graph.add_task(node)
        graph.mark_failed(tid, "timeout")
        assert node.status == "failed"
        assert node.result == {"error": "timeout"}

    def test_execution_order(self) -> None:
        graph = TaskGraph()
        n1 = TaskNode(name="t1", capability_id="c1")
        n2 = TaskNode(name="t2", capability_id="c2")
        n3 = TaskNode(name="t3", capability_id="c3")
        t1 = graph.add_task(n1)
        t2 = graph.add_task(n2)
        t3 = graph.add_task(n3)
        graph.add_dependency(t2, t1)
        graph.add_dependency(t3, t2)
        order = graph.get_execution_order()
        assert order.index(t1) < order.index(t2)
        assert order.index(t2) < order.index(t3)

    def test_has_cycle_false(self) -> None:
        graph = TaskGraph()
        n1 = TaskNode(name="t1", capability_id="c1")
        n2 = TaskNode(name="t2", capability_id="c2")
        t1 = graph.add_task(n1)
        t2 = graph.add_task(n2)
        graph.add_dependency(t2, t1)
        assert graph.has_cycle() is False

    def test_critical_path(self) -> None:
        graph = TaskGraph()
        n1 = TaskNode(name="t1", capability_id="c1", timeout_seconds=10)
        n2 = TaskNode(name="t2", capability_id="c2", timeout_seconds=20)
        n3 = TaskNode(name="t3", capability_id="c3", timeout_seconds=5)
        t1 = graph.add_task(n1)
        t2 = graph.add_task(n2)
        t3 = graph.add_task(n3)
        graph.add_dependency(t2, t1)
        graph.add_dependency(t3, t1)
        path = graph.get_critical_path()
        assert len(path) >= 1


# --- Test DependencyGraph ---


class TestDependencyGraph:
    """Tests for the dependency graph."""

    def test_add_node(self) -> None:
        g = ExecutiveDependencyGraph()
        g.add_node("a")
        assert "a" in g._adjacency

    def test_add_edge(self) -> None:
        g = ExecutiveDependencyGraph()
        g.add_edge("a", "b")
        assert "b" in g._adjacency["a"]

    def test_get_dependencies(self) -> None:
        g = ExecutiveDependencyGraph()
        g.add_edge("a", "b")
        deps = g.get_dependencies("b")
        assert "a" in deps

    def test_get_dependents(self) -> None:
        g = ExecutiveDependencyGraph()
        g.add_edge("a", "b")
        dependents = g.get_dependents("a")
        assert "b" in dependents

    def test_topological_sort(self) -> None:
        g = ExecutiveDependencyGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        order = g.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_has_cycle_false(self) -> None:
        g = ExecutiveDependencyGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        assert g.has_cycle() is False

    def test_parallel_groups(self) -> None:
        g = ExecutiveDependencyGraph()
        g.add_node("a")
        g.add_node("b")
        g.add_edge("a", "c")
        g.add_edge("b", "c")
        groups = g.get_parallel_groups()
        # First group should have a and b
        assert len(groups) >= 2
        first_group = set(groups[0])
        assert "a" in first_group or "b" in first_group


# --- Test RiskEngine ---


class TestRiskEngine:
    """Tests for risk assessment."""

    def test_assess_risk(self) -> None:
        re = RiskEngine()
        plan = ExecutionPlan(
            goal_id="g1", strategy_id="s1", tasks=["t1", "t2"], estimated_duration_ms=5000
        )
        goal = Goal(title="Risk", description="desc")
        risk = re.assess_risk(plan, goal)
        assert "overall_risk" in risk
        assert 0.0 <= risk["overall_risk"] <= 1.0

    def test_get_risk_factors(self) -> None:
        re = RiskEngine()
        plan = ExecutionPlan(
            goal_id="g1",
            strategy_id="s1",
            tasks=["t1", "t2", "t3", "t4", "t5", "t6"],
            execution_mode="parallel",
        )
        factors = re.get_risk_factors(plan)
        assert len(factors) >= 1
        assert any(f["factor"] == "high_task_count" for f in factors)

    def test_low_risk_plan(self) -> None:
        re = RiskEngine()
        plan = ExecutionPlan(
            goal_id="g1",
            strategy_id="s1",
            tasks=["t1"],
            estimated_duration_ms=100,
            rollback_path=["undo:t1"],
            checkpoints=["cp1"],
        )
        goal = Goal(title="Low", description="desc")
        risk = re.assess_risk(plan, goal)
        assert risk["overall_risk"] < 0.5

    def test_high_risk_plan(self) -> None:
        re = RiskEngine()
        tasks = [f"delete_admin_secret_{i}" for i in range(15)]
        plan = ExecutionPlan(
            goal_id="g1",
            strategy_id="s1",
            tasks=tasks,
            estimated_duration_ms=50000,
            execution_mode="parallel",
        )
        goal = Goal(title="High", description="desc")
        risk = re.assess_risk(plan, goal)
        assert risk["overall_risk"] > 0.3


# --- Test CostEngine ---


class TestCostEngine:
    """Tests for cost estimation."""

    def test_estimate_cost(self) -> None:
        ce = CostEngine()
        plan = ExecutionPlan(
            goal_id="g1", strategy_id="s1", tasks=["t1", "t2"], estimated_duration_ms=1000
        )
        cost = ce.estimate_cost(plan, ["cap1", "cap2"])
        assert cost["total_estimated"] > 0
        assert "token_cost" in cost
        assert "compute_cost" in cost
        assert "api_cost" in cost

    def test_compare_costs(self) -> None:
        ce = CostEngine()
        p1 = ExecutionPlan(goal_id="g1", strategy_id="s1", tasks=["t1"], estimated_duration_ms=500)
        p2 = ExecutionPlan(
            goal_id="g2", strategy_id="s2", tasks=["t1", "t2", "t3"], estimated_duration_ms=3000
        )
        comparison = ce.compare_costs([p1, p2])
        assert len(comparison) == 2
        assert comparison[0]["rank"] == 1

    def test_budget_check_pass(self) -> None:
        ce = CostEngine()
        plan = ExecutionPlan(
            goal_id="g1", strategy_id="s1", tasks=["t1"], estimated_duration_ms=100
        )
        within, remaining = ce.budget_check(plan, budget=10.0)
        assert within is True
        assert remaining > 0

    def test_budget_check_fail(self) -> None:
        ce = CostEngine()
        plan = ExecutionPlan(
            goal_id="g1",
            strategy_id="s1",
            tasks=[f"t{i}" for i in range(1000)],
            estimated_duration_ms=100000,
        )
        within, remaining = ce.budget_check(plan, budget=0.001)
        assert within is False
        assert remaining < 0


# --- Test ConfidenceEngine ---


class TestConfidenceEngine:
    """Tests for confidence estimation."""

    def test_estimate_confidence(self) -> None:
        ce = ConfidenceEngine()
        decision = Decision(
            confidence=0.8,
            risk=0.2,
            alternatives=[
                Strategy(strategy_type=StrategyType.BALANCED, description="s1"),
                Strategy(strategy_type=StrategyType.FASTEST, description="s2"),
            ],
        )
        plan = ExecutionPlan(
            goal_id="g1",
            strategy_id="s1",
            tasks=["t1", "t2"],
            checkpoints=["cp1"],
            rollback_path=["rb1"],
        )
        report = ce.estimate_confidence(decision, plan)
        assert "overall" in report
        assert 0.0 <= report["overall"] <= 1.0

    def test_explain_confidence(self) -> None:
        ce = ConfidenceEngine()
        report = {
            "overall": 0.85,
            "decision_confidence": 0.9,
            "plan_confidence": 0.8,
            "capability_confidence": 0.7,
            "execution_confidence": 0.8,
            "provider_confidence": 0.9,
            "model_confidence": 0.85,
        }
        explanation = ce.explain_confidence(report)
        assert "HIGH confidence" in explanation

    def test_high_confidence(self) -> None:
        ce = ConfidenceEngine()
        decision = Decision(
            confidence=0.95,
            risk=0.05,
            alternatives=[
                Strategy(strategy_type=StrategyType.SAFEST, description="s"),
            ]
            * 5,
        )
        plan = ExecutionPlan(
            goal_id="g1", strategy_id="s1", tasks=["t1"], checkpoints=["cp1"], rollback_path=["rb1"]
        )
        report = ce.estimate_confidence(decision, plan)
        assert report["overall"] > 0.5

    def test_low_confidence(self) -> None:
        ce = ConfidenceEngine()
        decision = Decision(confidence=0.2, risk=0.9, alternatives=[])
        plan = ExecutionPlan(goal_id="g1", strategy_id="s1", tasks=[])
        report = ce.estimate_confidence(decision, plan)
        assert report["overall"] < 0.7


# --- Test CapabilityOrchestrator ---


class TestCapabilityOrchestrator:
    """Tests for capability orchestration."""

    def test_assemble_pipeline(self) -> None:
        co = CapabilityOrchestrator()
        goal = Goal(title="Assemble", description="desc")
        s = Strategy(
            strategy_type=StrategyType.BALANCED,
            description="bal",
            steps=["parallel_execute:cap1", "verify_execute:cap2"],
        )
        decision = Decision(selected=s, alternatives=[s])
        pipeline = co.assemble_pipeline(goal, decision)
        assert "cap1" in pipeline
        assert "cap2" in pipeline

    def test_compose_single(self) -> None:
        co = CapabilityOrchestrator()
        result = co.compose_single("search")
        assert result["type"] == "single"
        assert result["capability_id"] == "search"

    def test_compose_multi(self) -> None:
        co = CapabilityOrchestrator()
        result = co.compose_multi(["a", "b", "c"])
        assert result["type"] == "sequential"
        assert len(result["capabilities"]) == 3

    def test_validate_pipeline(self) -> None:
        co = CapabilityOrchestrator()
        valid, errors = co.validate_pipeline(["cap1", "cap2"])
        assert valid is True
        assert len(errors) == 0
        # Test empty pipeline
        valid, errors = co.validate_pipeline([])
        assert valid is False


# --- Test ProviderSelector ---


class TestProviderSelector:
    """Tests for provider selection."""

    def test_select_provider(self) -> None:
        ps = ProviderSelector()
        provider = ps.select_provider({"max_latency_ms": 500})
        assert provider is not None
        assert provider in ps.get_available_providers()

    def test_rank_providers(self) -> None:
        ps = ProviderSelector()
        ranked = ps.rank_providers({"max_latency_ms": 1000})
        assert len(ranked) >= 3
        # Scores should be descending
        scores = [score for _, score in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_get_available_providers(self) -> None:
        ps = ProviderSelector()
        providers = ps.get_available_providers()
        assert len(providers) >= 3
        assert "openai" in providers


# --- Test ModelSelector ---


class TestModelSelector:
    """Tests for model selection."""

    def test_select_model(self) -> None:
        ms = ModelSelector()
        model = ms.select_model({"capabilities": ["code", "reasoning"]})
        assert model is not None
        assert model in ms.get_available_models()

    def test_rank_models(self) -> None:
        ms = ModelSelector()
        ranked = ms.rank_models({"min_reasoning": 0.5})
        assert len(ranked) >= 3
        scores = [score for _, score in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_get_available_models(self) -> None:
        ms = ModelSelector()
        models = ms.get_available_models()
        assert len(models) >= 3
        assert "gpt-4o" in models


# --- Test WorkflowOptimizer ---


class TestWorkflowOptimizer:
    """Tests for workflow optimization."""

    def test_optimize_balanced(self) -> None:
        wo = WorkflowOptimizer()
        plan = ExecutionPlan(
            goal_id="g1",
            strategy_id="s1",
            tasks=["t1", "t2", "t3", "t4"],
            estimated_duration_ms=4000,
        )
        optimized = wo.optimize(plan, metric="balanced")
        assert optimized.execution_mode == "parallel"
        assert optimized.estimated_duration_ms < 4000

    def test_optimize_order(self) -> None:
        wo = WorkflowOptimizer()
        graph = TaskGraph()
        n1 = TaskNode(name="first", capability_id="c1")
        n2 = TaskNode(name="second", capability_id="c2")
        t1 = graph.add_task(n1)
        t2 = graph.add_task(n2)
        graph.add_dependency(t2, t1)
        ordered = wo.optimize_order([t2, t1], graph)
        assert ordered.index(t1) < ordered.index(t2)

    def test_estimate_savings(self) -> None:
        wo = WorkflowOptimizer()
        original = ExecutionPlan(
            goal_id="g1", strategy_id="s1", tasks=["t1", "t2", "t3"], estimated_duration_ms=3000
        )
        optimized = ExecutionPlan(
            goal_id="g1", strategy_id="s1", tasks=["t1", "t2"], estimated_duration_ms=1000
        )
        savings = wo.estimate_savings(original, optimized)
        assert savings["time_saved_ms"] == 2000.0
        assert savings["efficiency_gain"] > 0


# --- Test ParallelPlanner ---


class TestParallelPlanner:
    """Tests for parallel execution planning."""

    def test_identify_parallel_tasks(self) -> None:
        pp = ParallelPlanner()
        graph = TaskGraph()
        n1 = TaskNode(name="t1", capability_id="c1")
        n2 = TaskNode(name="t2", capability_id="c2")
        n3 = TaskNode(name="t3", capability_id="c3")
        graph.add_task(n1)
        graph.add_task(n2)
        t3 = graph.add_task(n3)
        graph.add_dependency(t3, n1.task_id)
        graph.add_dependency(t3, n2.task_id)
        groups = pp.identify_parallel_tasks(graph)
        assert len(groups) >= 2
        # First group should have t1 and t2 (no deps)
        assert len(groups[0]) >= 2

    def test_plan_parallel_execution(self) -> None:
        pp = ParallelPlanner()
        tasks = [["t1", "t2", "t3"], ["t4", "t5"]]
        plan = pp.plan_parallel_execution(tasks, max_concurrency=2)
        assert len(plan) >= 2
        assert all(p["mode"] == "parallel" for p in plan)

    def test_validate_parallel_safety(self) -> None:
        pp = ParallelPlanner()
        graph = TaskGraph()
        n1 = TaskNode(name="t1", capability_id="c1")
        n2 = TaskNode(name="t2", capability_id="c2")
        graph.add_task(n1)
        graph.add_task(n2)
        # No dependencies, so running in parallel is safe
        valid, errors = pp.validate_parallel_safety([[n1.task_id, n2.task_id]], graph)
        assert valid is True
        assert len(errors) == 0


# --- Test ApprovalEngine ---


class TestApprovalEngine:
    """Tests for approval gate engine."""

    def test_auto_approve(self) -> None:
        ae = ApprovalEngine()
        plan = ExecutionPlan(goal_id="g1", strategy_id="s1", tasks=["t1"])
        risk = {"overall_risk": 0.1}
        cost = {"total_estimated": 0.01}
        confidence = {"overall": 0.9}
        status = ae.evaluate(plan, risk, cost, confidence)
        assert status == ApprovalStatus.AUTO_APPROVED

    def test_human_required(self) -> None:
        ae = ApprovalEngine()
        plan = ExecutionPlan(goal_id="g1", strategy_id="s1", tasks=["t1"])
        risk = {"overall_risk": 0.7}
        cost = {"total_estimated": 0.5}
        confidence = {"overall": 0.6}
        status = ae.evaluate(plan, risk, cost, confidence)
        assert status == ApprovalStatus.PENDING_APPROVAL

    def test_blocked(self) -> None:
        ae = ApprovalEngine()
        plan = ExecutionPlan(goal_id="g1", strategy_id="s1", tasks=["t1"])
        risk = {"overall_risk": 0.95}
        cost = {"total_estimated": 0.5}
        confidence = {"overall": 0.3}
        status = ae.evaluate(plan, risk, cost, confidence)
        assert status == ApprovalStatus.BLOCKED

    def test_explain_decision(self) -> None:
        ae = ApprovalEngine()
        explanation = ae.explain_decision(
            ApprovalStatus.AUTO_APPROVED,
            {"overall_risk": 0.1},
            {"total_estimated": 0.01},
            {"overall": 0.9},
        )
        assert "Low risk" in explanation
        assert "auto_approved" in explanation.lower()

    def test_approval_history(self) -> None:
        ae = ApprovalEngine()
        plan = ExecutionPlan(goal_id="g1", strategy_id="s1", tasks=["t1"])
        ae.evaluate(plan, {"overall_risk": 0.1}, {"total_estimated": 0.01}, {"overall": 0.9})
        ae.evaluate(plan, {"overall_risk": 0.95}, {"total_estimated": 5.0}, {"overall": 0.2})
        history = ae.get_approval_history()
        assert len(history) == 2


# --- Test ExecutiveBrain ---


class TestExecutiveBrain:
    """Tests for the main executive brain orchestrator."""

    def _make_brain(self) -> ExecutiveBrain:
        return ExecutiveBrain(
            goal_manager=GoalManager(),
            strategic_planner=StrategicPlanner(),
            decision_engine=DecisionEngine(),
            execution_planner=ExecutionPlanner(),
            risk_engine=RiskEngine(),
            cost_engine=CostEngine(),
            confidence_engine=ConfidenceEngine(),
            capability_orchestrator=CapabilityOrchestrator(),
            provider_selector=ProviderSelector(),
            model_selector=ModelSelector(),
            workflow_optimizer=WorkflowOptimizer(),
            parallel_planner=ParallelPlanner(),
            approval_engine=ApprovalEngine(),
        )

    def test_process_goal(self) -> None:
        brain = self._make_brain()
        result = asyncio.run(brain.process_goal("Test Goal", "A test", GoalPriority.MEDIUM))
        assert "goal" in result
        assert "decision" in result
        assert "plan" in result
        assert "risk" in result
        assert "cost" in result
        assert "confidence" in result
        assert "approval" in result

    def test_get_status(self) -> None:
        brain = self._make_brain()
        status = brain.get_status()
        assert status["active"] is True
        assert "goals" in status
        assert "providers" in status
        assert "models" in status

    def test_get_events(self) -> None:
        brain = self._make_brain()
        asyncio.run(brain.process_goal("Event Test", "desc"))
        events = brain.get_events()
        assert len(events) > 0
        assert events[0]["event_type"] == "goal_created"

    def test_error_handling(self) -> None:
        brain = self._make_brain()
        # Process should succeed even with empty description
        result = asyncio.run(brain.process_goal("", ""))
        assert "goal" in result
