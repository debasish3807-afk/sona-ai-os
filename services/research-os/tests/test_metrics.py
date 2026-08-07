"""Tests for personal AI metrics."""

import pytest

from sona_research.infrastructure.metrics import PersonalAIMetrics


@pytest.fixture
def metrics() -> PersonalAIMetrics:
    return PersonalAIMetrics()


class TestMetricsCounters:
    def test_increment_default(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("test_counter")
        assert metrics.get_counter("test_counter") == 1.0

    def test_increment_custom_value(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("test_counter", 5.0)
        assert metrics.get_counter("test_counter") == 5.0

    def test_increment_accumulates(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("counter")
        metrics.increment("counter")
        metrics.increment("counter")
        assert metrics.get_counter("counter") == 3.0

    def test_counter_with_labels(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("requests", labels={"method": "GET"})
        metrics.increment("requests", labels={"method": "POST"})
        assert metrics.get_counter("requests", labels={"method": "GET"}) == 1.0
        assert metrics.get_counter("requests", labels={"method": "POST"}) == 1.0

    def test_get_nonexistent_counter(self, metrics: PersonalAIMetrics) -> None:
        assert metrics.get_counter("nonexistent") == 0.0


class TestMetricsGauges:
    def test_set_gauge(self, metrics: PersonalAIMetrics) -> None:
        metrics.set_gauge("temperature", 72.5)
        assert metrics.get_gauge("temperature") == 72.5

    def test_gauge_overwrite(self, metrics: PersonalAIMetrics) -> None:
        metrics.set_gauge("value", 10.0)
        metrics.set_gauge("value", 20.0)
        assert metrics.get_gauge("value") == 20.0

    def test_gauge_with_labels(self, metrics: PersonalAIMetrics) -> None:
        metrics.set_gauge("cpu", 80.0, labels={"core": "0"})
        metrics.set_gauge("cpu", 60.0, labels={"core": "1"})
        assert metrics.get_gauge("cpu", labels={"core": "0"}) == 80.0
        assert metrics.get_gauge("cpu", labels={"core": "1"}) == 60.0

    def test_get_nonexistent_gauge(self, metrics: PersonalAIMetrics) -> None:
        assert metrics.get_gauge("nonexistent") == 0.0


class TestMetricsHistory:
    def test_records_history(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("action")
        history = metrics.get_history("action")
        assert len(history) == 1
        assert history[0].name == "action"

    def test_history_filter_by_name(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("a")
        metrics.increment("b")
        assert len(metrics.get_history("a")) == 1
        assert len(metrics.get_history("b")) == 1

    def test_history_all(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("x")
        metrics.set_gauge("y", 1.0)
        all_history = metrics.get_history()
        assert len(all_history) == 2


class TestMetricsConvenience:
    def test_record_note_created(self, metrics: PersonalAIMetrics) -> None:
        metrics.record_note_created()
        metrics.record_note_created()
        assert metrics.get_counter("notes_created_total") == 2.0

    def test_record_task_created(self, metrics: PersonalAIMetrics) -> None:
        metrics.record_task_created("high")
        assert metrics.get_counter("tasks_created_total", labels={"priority": "high"}) == 1.0

    def test_record_search(self, metrics: PersonalAIMetrics) -> None:
        metrics.record_search_performed("notes")
        assert metrics.get_counter("searches_total", labels={"subsystem": "notes"}) == 1.0

    def test_record_document_indexed(self, metrics: PersonalAIMetrics) -> None:
        metrics.record_document_indexed("markdown")
        assert metrics.get_counter("documents_indexed_total", labels={"format": "markdown"}) == 1.0

    def test_record_graph_node(self, metrics: PersonalAIMetrics) -> None:
        metrics.record_graph_node_added("concept")
        assert metrics.get_counter("graph_nodes_added_total", labels={"type": "concept"}) == 1.0

    def test_record_github_op(self, metrics: PersonalAIMetrics) -> None:
        metrics.record_github_operation("index_repository")
        assert (
            metrics.get_counter("github_operations_total", labels={"operation": "index_repository"})
            == 1.0
        )

    def test_record_error(self, metrics: PersonalAIMetrics) -> None:
        metrics.record_error("notes", "not_found")
        assert (
            metrics.get_counter("errors_total", labels={"subsystem": "notes", "type": "not_found"})
            == 1.0
        )

    def test_update_notes_count(self, metrics: PersonalAIMetrics) -> None:
        metrics.update_notes_count(5)
        assert metrics.get_gauge("notes_count") == 5.0

    def test_update_tasks_count(self, metrics: PersonalAIMetrics) -> None:
        metrics.update_tasks_count(3, "done")
        assert metrics.get_gauge("tasks_count", labels={"status": "done"}) == 3.0

    def test_update_graph_size(self, metrics: PersonalAIMetrics) -> None:
        metrics.update_graph_size(10, 5)
        assert metrics.get_gauge("graph_nodes_count") == 10.0
        assert metrics.get_gauge("graph_edges_count") == 5.0


class TestMetricsReset:
    def test_reset(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("counter")
        metrics.set_gauge("gauge", 1.0)
        metrics.reset()
        assert metrics.get_counter("counter") == 0.0
        assert metrics.get_gauge("gauge") == 0.0
        assert metrics.get_history() == []

    def test_get_all_counters(self, metrics: PersonalAIMetrics) -> None:
        metrics.increment("a")
        metrics.increment("b")
        all_counters = metrics.get_all_counters()
        assert "a" in all_counters
        assert "b" in all_counters

    def test_get_all_gauges(self, metrics: PersonalAIMetrics) -> None:
        metrics.set_gauge("x", 1.0)
        metrics.set_gauge("y", 2.0)
        all_gauges = metrics.get_all_gauges()
        assert all_gauges["x"] == 1.0
        assert all_gauges["y"] == 2.0
