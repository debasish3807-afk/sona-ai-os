"""Unit tests for Workflow Engine domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability where specified.
"""

import pytest

from domain.models import (
    StepStatus,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
)


class TestStepStatus:
    """Tests for the StepStatus enum."""

    def test_all_values_defined(self) -> None:
        """Verify all required step statuses exist."""
        expected = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED", "WAITING"}
        actual = {member.name for member in StepStatus}
        assert actual == expected

    def test_string_values(self) -> None:
        """Verify enum values are the correct strings."""
        assert StepStatus.PENDING == "pending"
        assert StepStatus.RUNNING == "running"
        assert StepStatus.COMPLETED == "completed"
        assert StepStatus.FAILED == "failed"
        assert StepStatus.SKIPPED == "skipped"
        assert StepStatus.WAITING == "waiting_for_input"

    def test_is_str_enum(self) -> None:
        """Verify StepStatus is a StrEnum and can be used as string."""
        assert isinstance(StepStatus.PENDING, str)
        assert f"Status: {StepStatus.RUNNING}" == "Status: running"

    def test_total_count(self) -> None:
        """Verify the correct number of step statuses."""
        assert len(StepStatus) == 6


class TestWorkflowStep:
    """Tests for the WorkflowStep frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        step = WorkflowStep(
            step_id="step-1",
            name="Fetch data",
            action="http_request",
            params={"url": "https://api.example.com/data"},
        )
        assert step.step_id == "step-1"
        assert step.name == "Fetch data"
        assert step.action == "http_request"
        assert step.params == {"url": "https://api.example.com/data"}

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        step = WorkflowStep(
            step_id="s1",
            name="Process",
            action="transform",
            params={},
        )
        assert step.depends_on == ()
        assert step.retry_count == 3
        assert step.timeout_seconds == 300
        assert step.condition is None

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        step = WorkflowStep(
            step_id="step-2",
            name="Process data",
            action="agent_call",
            params={"agent": "coding", "instruction": "Parse JSON"},
            depends_on=["step-1"],
            retry_count=5,
            timeout_seconds=600,
            condition="step-1.status == 'completed'",
        )
        assert step.depends_on == ["step-1"]
        assert step.retry_count == 5
        assert step.timeout_seconds == 600
        assert step.condition == "step-1.status == 'completed'"

    def test_is_frozen(self) -> None:
        """Verify WorkflowStep is immutable."""
        step = WorkflowStep(
            step_id="s1",
            name="Test",
            action="noop",
            params={},
        )
        with pytest.raises(Exception):
            step.step_id = "changed"  # type: ignore[misc]

    def test_depends_on_multiple_steps(self) -> None:
        """Verify a step can depend on multiple prior steps."""
        step = WorkflowStep(
            step_id="step-3",
            name="Merge results",
            action="merge",
            params={"strategy": "concat"},
            depends_on=["step-1", "step-2"],
        )
        assert len(step.depends_on) == 2
        assert "step-1" in step.depends_on
        assert "step-2" in step.depends_on


class TestWorkflowDefinition:
    """Tests for the WorkflowDefinition frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        defn = WorkflowDefinition(
            workflow_id="wf-001",
            name="Data Pipeline",
            description="Fetches and processes data from API",
        )
        assert defn.workflow_id == "wf-001"
        assert defn.name == "Data Pipeline"
        assert defn.description == "Fetches and processes data from API"

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        defn = WorkflowDefinition(
            workflow_id="wf-1",
            name="Test",
            description="A test workflow",
        )
        assert defn.steps == ()
        assert defn.trigger is None
        assert defn.schedule is None

    def test_with_steps(self) -> None:
        """Create with workflow steps."""
        steps = [
            WorkflowStep(
                step_id="s1",
                name="Fetch",
                action="http_get",
                params={"url": "https://example.com"},
            ),
            WorkflowStep(
                step_id="s2",
                name="Process",
                action="transform",
                params={"format": "json"},
                depends_on=["s1"],
            ),
        ]
        defn = WorkflowDefinition(
            workflow_id="wf-002",
            name="ETL Pipeline",
            description="Extract, transform, load",
            steps=steps,
        )
        assert len(defn.steps) == 2
        assert defn.steps[0].step_id == "s1"
        assert defn.steps[1].depends_on == ["s1"]

    def test_with_trigger_and_schedule(self) -> None:
        """Create with trigger and schedule fields."""
        defn = WorkflowDefinition(
            workflow_id="wf-003",
            name="Scheduled Report",
            description="Generates daily report",
            trigger="document.uploaded",
            schedule="0 9 * * *",
        )
        assert defn.trigger == "document.uploaded"
        assert defn.schedule == "0 9 * * *"

    def test_is_frozen(self) -> None:
        """Verify WorkflowDefinition is immutable."""
        defn = WorkflowDefinition(
            workflow_id="wf-1",
            name="Test",
            description="Test workflow",
        )
        with pytest.raises(Exception):
            defn.name = "changed"  # type: ignore[misc]


class TestWorkflowExecution:
    """Tests for the WorkflowExecution dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        execution = WorkflowExecution(
            execution_id="exec-001",
            workflow_id="wf-001",
            status=StepStatus.PENDING,
        )
        assert execution.execution_id == "exec-001"
        assert execution.workflow_id == "wf-001"
        assert execution.status == StepStatus.PENDING

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        execution = WorkflowExecution(
            execution_id="e1",
            workflow_id="wf-1",
            status=StepStatus.RUNNING,
        )
        assert execution.current_step is None
        assert execution.results is None
        assert execution.started_at is None
        assert execution.completed_at is None

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        execution = WorkflowExecution(
            execution_id="exec-xyz",
            workflow_id="wf-002",
            status=StepStatus.COMPLETED,
            current_step="step-3",
            results={"step-1": {"output": "data"}, "step-2": {"output": "processed"}},
            started_at="2024-01-15T10:00:00Z",
            completed_at="2024-01-15T10:05:30Z",
        )
        assert execution.current_step == "step-3"
        assert execution.results["step-1"] == {"output": "data"}
        assert execution.started_at == "2024-01-15T10:00:00Z"
        assert execution.completed_at == "2024-01-15T10:05:30Z"

    def test_is_mutable(self) -> None:
        """Verify WorkflowExecution is mutable (not frozen)."""
        execution = WorkflowExecution(
            execution_id="e1",
            workflow_id="wf-1",
            status=StepStatus.PENDING,
        )
        execution.status = StepStatus.RUNNING
        execution.current_step = "step-1"
        execution.started_at = "2024-01-15T10:00:00Z"
        assert execution.status == StepStatus.RUNNING
        assert execution.current_step == "step-1"

    def test_status_uses_step_status_enum(self) -> None:
        """Verify status field accepts StepStatus enum values."""
        execution = WorkflowExecution(
            execution_id="e1",
            workflow_id="wf-1",
            status=StepStatus.WAITING,
        )
        assert execution.status == StepStatus.WAITING
        assert execution.status == "waiting_for_input"

    def test_failed_execution(self) -> None:
        """Verify execution can represent a failed state."""
        execution = WorkflowExecution(
            execution_id="exec-fail",
            workflow_id="wf-001",
            status=StepStatus.FAILED,
            current_step="step-2",
            results={"step-1": {"output": "ok"}, "step-2": {"error": "timeout"}},
            started_at="2024-01-15T10:00:00Z",
            completed_at="2024-01-15T10:02:00Z",
        )
        assert execution.status == StepStatus.FAILED
        assert "error" in execution.results["step-2"]
