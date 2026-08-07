"""Personal AI metrics for monitoring and observability.

Provides metrics collection for the Personal AI Runtime,
tracking usage, performance, and health indicators.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog

logger = structlog.get_logger()


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: float
    timestamp: str = ""
    labels: dict[str, str] = field(default_factory=dict)


class PersonalAIMetrics:
    """Metrics collector for Personal AI Runtime.

    Tracks operations, errors, and timing for all subsystems.
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._history: list[MetricPoint] = []

    def increment(
        self, name: str, value: float = 1.0, labels: dict[str, str] | None = None
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Metric name.
            value: Value to increment by.
            labels: Optional labels for the metric.
        """
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0.0) + value
        self._record_point(name, self._counters[key], labels)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric to a specific value.

        Args:
            name: Metric name.
            value: Value to set.
            labels: Optional labels for the metric.
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value
        self._record_point(name, value, labels)

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get current counter value.

        Args:
            name: Metric name.
            labels: Optional labels.

        Returns:
            Current counter value, 0.0 if not set.
        """
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get current gauge value.

        Args:
            name: Metric name.
            labels: Optional labels.

        Returns:
            Current gauge value, 0.0 if not set.
        """
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_history(self, name: str | None = None) -> list[MetricPoint]:
        """Get metric history, optionally filtered by name.

        Args:
            name: Optional metric name filter.

        Returns:
            List of metric data points.
        """
        if name is None:
            return list(self._history)
        return [p for p in self._history if p.name == name]

    def get_all_counters(self) -> dict[str, float]:
        """Get all counter values.

        Returns:
            Dictionary of counter keys to values.
        """
        return dict(self._counters)

    def get_all_gauges(self) -> dict[str, float]:
        """Get all gauge values.

        Returns:
            Dictionary of gauge keys to values.
        """
        return dict(self._gauges)

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._history.clear()

    def _make_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        """Create a unique key from metric name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _record_point(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a metric data point in history."""
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(UTC).isoformat(),
            labels=labels or {},
        )
        self._history.append(point)

    # Convenience methods for common operations

    def record_note_created(self) -> None:
        """Record a note creation event."""
        self.increment("notes_created_total")

    def record_task_created(self, priority: str = "medium") -> None:
        """Record a task creation event."""
        self.increment("tasks_created_total", labels={"priority": priority})

    def record_search_performed(self, subsystem: str = "general") -> None:
        """Record a search operation."""
        self.increment("searches_total", labels={"subsystem": subsystem})

    def record_document_indexed(self, format: str = "text") -> None:
        """Record a document indexing event."""
        self.increment("documents_indexed_total", labels={"format": format})

    def record_graph_node_added(self, node_type: str = "unknown") -> None:
        """Record a knowledge graph node addition."""
        self.increment("graph_nodes_added_total", labels={"type": node_type})

    def record_graph_edge_added(self, relationship: str = "unknown") -> None:
        """Record a knowledge graph edge addition."""
        self.increment("graph_edges_added_total", labels={"relationship": relationship})

    def record_github_operation(self, operation: str = "unknown") -> None:
        """Record a GitHub operation."""
        self.increment("github_operations_total", labels={"operation": operation})

    def record_error(self, subsystem: str, error_type: str = "unknown") -> None:
        """Record an error event."""
        self.increment("errors_total", labels={"subsystem": subsystem, "type": error_type})

    def update_notes_count(self, count: int) -> None:
        """Update the current notes count gauge."""
        self.set_gauge("notes_count", float(count))

    def update_tasks_count(self, count: int, status: str = "all") -> None:
        """Update the current tasks count gauge."""
        self.set_gauge("tasks_count", float(count), labels={"status": status})

    def update_graph_size(self, nodes: int, edges: int) -> None:
        """Update the knowledge graph size gauges."""
        self.set_gauge("graph_nodes_count", float(nodes))
        self.set_gauge("graph_edges_count", float(edges))
