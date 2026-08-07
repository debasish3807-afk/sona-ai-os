"""Unit tests for WorkforceMetrics."""

import pytest

from sona_workforce.infrastructure.metrics import AgentMetrics, WorkforceMetrics


class TestAgentMetrics:
    def test_default_values(self) -> None:
        m = AgentMetrics(agent_id="a1")
        assert m.tasks_total == 0
        assert m.tasks_success == 0
        assert m.tasks_failed == 0
        assert m.execution_duration_ms_total == 0.0
        assert m.tokens_used_total == 0


class TestWorkforceMetrics:
    @pytest.fixture
    def metrics(self) -> WorkforceMetrics:
        return WorkforceMetrics()

    def test_initial_state(self, metrics: WorkforceMetrics) -> None:
        assert metrics.agent_tasks_total == 0
        assert metrics.agent_failures_total == 0
        assert metrics.agent_execution_duration_ms == 0.0

    def test_record_task_completion(self, metrics: WorkforceMetrics) -> None:
        metrics.record_task_completion("a1", duration_ms=100.0, tokens_used=50)
        assert metrics.agent_tasks_total == 1
        assert metrics.agent_execution_duration_ms == 100.0

    def test_record_task_failure(self, metrics: WorkforceMetrics) -> None:
        metrics.record_task_failure("a1", duration_ms=50.0)
        assert metrics.agent_tasks_total == 1
        assert metrics.agent_failures_total == 1

    def test_per_agent_stats_completion(self, metrics: WorkforceMetrics) -> None:
        metrics.record_task_completion("a1", duration_ms=100.0, tokens_used=50)
        stats = metrics.get_agent_stats("a1")
        assert stats is not None
        assert stats.tasks_total == 1
        assert stats.tasks_success == 1
        assert stats.tokens_used_total == 50

    def test_per_agent_stats_failure(self, metrics: WorkforceMetrics) -> None:
        metrics.record_task_failure("a1", duration_ms=50.0)
        stats = metrics.get_agent_stats("a1")
        assert stats is not None
        assert stats.tasks_failed == 1

    def test_get_agent_stats_unknown(self, metrics: WorkforceMetrics) -> None:
        assert metrics.get_agent_stats("unknown") is None

    def test_get_all_agent_stats(self, metrics: WorkforceMetrics) -> None:
        metrics.record_task_completion("a1", 100.0, 50)
        metrics.record_task_completion("a2", 200.0, 100)
        all_stats = metrics.get_all_agent_stats()
        assert len(all_stats) == 2
        assert "a1" in all_stats
        assert "a2" in all_stats

    def test_update_queue_depth(self, metrics: WorkforceMetrics) -> None:
        metrics.update_queue_depth(5)
        assert metrics.agent_queue_depth == 5

    def test_update_active_count(self, metrics: WorkforceMetrics) -> None:
        metrics.update_active_count(3)
        assert metrics.agent_active_count == 3

    def test_get_summary(self, metrics: WorkforceMetrics) -> None:
        metrics.record_task_completion("a1", 100.0, 50)
        metrics.record_task_completion("a1", 200.0, 100)
        metrics.record_task_failure("a2", 50.0)
        metrics.update_queue_depth(2)
        metrics.update_active_count(1)
        summary = metrics.get_summary()
        assert summary["tasks_total"] == 3
        assert summary["failures_total"] == 1
        assert summary["avg_duration_ms"] == pytest.approx(116.67, rel=0.01)
        assert summary["success_rate"] == pytest.approx(0.6667, rel=0.01)
        assert summary["queue_depth"] == 2
        assert summary["active_count"] == 1
        assert summary["agents_tracked"] == 2

    def test_get_summary_empty(self, metrics: WorkforceMetrics) -> None:
        summary = metrics.get_summary()
        assert summary["tasks_total"] == 0
        assert summary["avg_duration_ms"] == 0.0
        assert summary["success_rate"] == 0.0

    def test_multiple_completions_same_agent(self, metrics: WorkforceMetrics) -> None:
        metrics.record_task_completion("a1", 100.0, 50)
        metrics.record_task_completion("a1", 200.0, 100)
        stats = metrics.get_agent_stats("a1")
        assert stats is not None
        assert stats.tasks_total == 2
        assert stats.tasks_success == 2
        assert stats.execution_duration_ms_total == 300.0
        assert stats.tokens_used_total == 150

    def test_mixed_success_failure(self, metrics: WorkforceMetrics) -> None:
        metrics.record_task_completion("a1", 100.0, 50)
        metrics.record_task_failure("a1", 50.0)
        stats = metrics.get_agent_stats("a1")
        assert stats is not None
        assert stats.tasks_total == 2
        assert stats.tasks_success == 1
        assert stats.tasks_failed == 1
