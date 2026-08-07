"""Unit tests for the ExecutionGraph."""

import pytest

from sona_thalamus.domain.execution_plan import ExecutionStep, ExecutionStepType
from sona_thalamus.infrastructure.execution_graph import CyclicDependencyError, ExecutionGraph


class TestExecutionGraph:
    """Tests for execution graph operations."""

    def _make_step(
        self,
        step_id: str,
        depends_on: list[str] | None = None,
        timeout: float = 10.0,
        priority: int = 5,
    ) -> ExecutionStep:
        """Create a test execution step."""
        return ExecutionStep(
            step_id=step_id,
            step_type=ExecutionStepType.LLM_CALL,
            target="test-model",
            depends_on=depends_on or [],
            timeout_seconds=timeout,
            priority=priority,
        )

    def test_add_step(self) -> None:
        """Test adding steps to graph."""
        graph = ExecutionGraph()
        step = self._make_step("step1")
        graph.add_step(step)
        assert graph.step_count == 1

    def test_topological_sort_no_deps(self) -> None:
        """Test topological sort with no dependencies."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a", priority=2))
        graph.add_step(self._make_step("b", priority=1))
        graph.add_step(self._make_step("c", priority=3))
        sorted_steps = graph.topological_sort()
        assert len(sorted_steps) == 3
        # Lower priority number first
        assert sorted_steps[0].step_id == "b"

    def test_topological_sort_with_deps(self) -> None:
        """Test topological sort respects dependencies."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a"))
        graph.add_step(self._make_step("b", depends_on=["a"]))
        graph.add_step(self._make_step("c", depends_on=["b"]))
        sorted_steps = graph.topological_sort()
        step_ids = [s.step_id for s in sorted_steps]
        assert step_ids.index("a") < step_ids.index("b")
        assert step_ids.index("b") < step_ids.index("c")

    def test_topological_sort_diamond(self) -> None:
        """Test diamond dependency graph."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a"))
        graph.add_step(self._make_step("b", depends_on=["a"]))
        graph.add_step(self._make_step("c", depends_on=["a"]))
        graph.add_step(self._make_step("d", depends_on=["b", "c"]))
        sorted_steps = graph.topological_sort()
        step_ids = [s.step_id for s in sorted_steps]
        assert step_ids.index("a") < step_ids.index("b")
        assert step_ids.index("a") < step_ids.index("c")
        assert step_ids.index("b") < step_ids.index("d")
        assert step_ids.index("c") < step_ids.index("d")

    def test_cycle_detection(self) -> None:
        """Test that cycles are detected."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a", depends_on=["b"]))
        graph.add_step(self._make_step("b", depends_on=["a"]))
        with pytest.raises(CyclicDependencyError):
            graph.topological_sort()

    def test_validate_valid_graph(self) -> None:
        """Test validate returns True for valid DAG."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a"))
        graph.add_step(self._make_step("b", depends_on=["a"]))
        assert graph.validate() is True

    def test_validate_invalid_graph(self) -> None:
        """Test validate returns False for cyclic graph."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a", depends_on=["b"]))
        graph.add_step(self._make_step("b", depends_on=["a"]))
        assert graph.validate() is False

    def test_parallel_groups_independent(self) -> None:
        """Test parallel groups for independent steps."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a"))
        graph.add_step(self._make_step("b"))
        graph.add_step(self._make_step("c"))
        groups = graph.get_parallel_groups()
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_parallel_groups_sequential(self) -> None:
        """Test parallel groups for fully sequential steps."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a"))
        graph.add_step(self._make_step("b", depends_on=["a"]))
        graph.add_step(self._make_step("c", depends_on=["b"]))
        groups = graph.get_parallel_groups()
        assert len(groups) == 3
        assert all(len(g) == 1 for g in groups)

    def test_parallel_groups_mixed(self) -> None:
        """Test parallel groups with mixed dependencies."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a"))
        graph.add_step(self._make_step("b", depends_on=["a"]))
        graph.add_step(self._make_step("c", depends_on=["a"]))
        graph.add_step(self._make_step("d", depends_on=["b", "c"]))
        groups = graph.get_parallel_groups()
        assert len(groups) == 3
        assert len(groups[0]) == 1  # a
        assert len(groups[1]) == 2  # b, c parallel
        assert len(groups[2]) == 1  # d

    def test_critical_path_latency(self) -> None:
        """Test critical path latency estimation."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a", timeout=5.0))
        graph.add_step(self._make_step("b", depends_on=["a"], timeout=10.0))
        latency = graph.estimate_critical_path_latency()
        assert latency == 15.0

    def test_critical_path_parallel(self) -> None:
        """Test critical path with parallel branches."""
        graph = ExecutionGraph()
        graph.add_step(self._make_step("a", timeout=5.0))
        graph.add_step(self._make_step("b", depends_on=["a"], timeout=10.0))
        graph.add_step(self._make_step("c", depends_on=["a"], timeout=3.0))
        latency = graph.estimate_critical_path_latency()
        # Critical path is a(5) -> b(10) = 15, not a(5) -> c(3) = 8
        assert latency == 15.0

    def test_empty_graph_latency(self) -> None:
        """Test latency estimation for empty graph."""
        graph = ExecutionGraph()
        assert graph.estimate_critical_path_latency() == 0.0

    def test_empty_graph_parallel_groups(self) -> None:
        """Test parallel groups for empty graph."""
        graph = ExecutionGraph()
        assert graph.get_parallel_groups() == []
