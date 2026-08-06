"""Unit tests for Workflow Engine abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest
from application.ports import WorkflowEnginePort
from domain.models import (
    StepStatus,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
)


class TestWorkflowEnginePort:
    """Tests for the WorkflowEnginePort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify WorkflowEnginePort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            WorkflowEnginePort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = WorkflowEnginePort.__abstractmethods__
        assert "create_workflow" in abstract_methods
        assert "execute" in abstract_methods
        assert "get_status" in abstract_methods
        assert "cancel" in abstract_methods
        assert "resume" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteEngine(WorkflowEnginePort):
            async def create_workflow(self, definition: WorkflowDefinition) -> str:
                return definition.workflow_id

            async def execute(self, workflow_id: str, inputs: dict) -> str:
                return f"exec-{workflow_id}"

            async def get_status(self, execution_id: str) -> WorkflowExecution:
                return WorkflowExecution(
                    execution_id=execution_id,
                    workflow_id="wf-1",
                    status=StepStatus.PENDING,
                )

            async def cancel(self, execution_id: str) -> bool:
                return True

            async def resume(self, execution_id: str, input_data: dict) -> bool:
                return True

        engine = ConcreteEngine()
        assert isinstance(engine, WorkflowEnginePort)

    def test_partial_implementation_raises(self) -> None:
        """Verify partial implementations cannot be instantiated."""

        class PartialEngine(WorkflowEnginePort):
            async def create_workflow(self, definition: WorkflowDefinition) -> str:
                return definition.workflow_id

            async def execute(self, workflow_id: str, inputs: dict) -> str:
                return f"exec-{workflow_id}"

        with pytest.raises(TypeError):
            PartialEngine()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_create_workflow_returns_id(self) -> None:
        """Test that create_workflow returns a workflow_id."""

        class MockEngine(WorkflowEnginePort):
            async def create_workflow(self, definition: WorkflowDefinition) -> str:
                return definition.workflow_id

            async def execute(self, workflow_id: str, inputs: dict) -> str:
                return f"exec-{workflow_id}"

            async def get_status(self, execution_id: str) -> WorkflowExecution:
                return WorkflowExecution(
                    execution_id=execution_id,
                    workflow_id="wf-1",
                    status=StepStatus.PENDING,
                )

            async def cancel(self, execution_id: str) -> bool:
                return True

            async def resume(self, execution_id: str, input_data: dict) -> bool:
                return True

        engine = MockEngine()
        definition = WorkflowDefinition(
            workflow_id="wf-test",
            name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    step_id="s1",
                    name="Step 1",
                    action="noop",
                    params={},
                )
            ],
        )
        result = await engine.create_workflow(definition)
        assert result == "wf-test"

    @pytest.mark.asyncio
    async def test_execute_returns_execution_id(self) -> None:
        """Test that execute returns an execution_id."""

        class MockEngine(WorkflowEnginePort):
            async def create_workflow(self, definition: WorkflowDefinition) -> str:
                return definition.workflow_id

            async def execute(self, workflow_id: str, inputs: dict) -> str:
                return f"exec-{workflow_id}-001"

            async def get_status(self, execution_id: str) -> WorkflowExecution:
                return WorkflowExecution(
                    execution_id=execution_id,
                    workflow_id="wf-1",
                    status=StepStatus.RUNNING,
                )

            async def cancel(self, execution_id: str) -> bool:
                return True

            async def resume(self, execution_id: str, input_data: dict) -> bool:
                return True

        engine = MockEngine()
        exec_id = await engine.execute("wf-test", {"input_key": "value"})
        assert exec_id == "exec-wf-test-001"
        assert isinstance(exec_id, str)

    @pytest.mark.asyncio
    async def test_get_status_returns_execution(self) -> None:
        """Test that get_status returns a WorkflowExecution."""

        class MockEngine(WorkflowEnginePort):
            async def create_workflow(self, definition: WorkflowDefinition) -> str:
                return definition.workflow_id

            async def execute(self, workflow_id: str, inputs: dict) -> str:
                return "exec-001"

            async def get_status(self, execution_id: str) -> WorkflowExecution:
                return WorkflowExecution(
                    execution_id=execution_id,
                    workflow_id="wf-1",
                    status=StepStatus.RUNNING,
                    current_step="step-2",
                    started_at="2024-01-15T10:00:00Z",
                )

            async def cancel(self, execution_id: str) -> bool:
                return True

            async def resume(self, execution_id: str, input_data: dict) -> bool:
                return True

        engine = MockEngine()
        status = await engine.get_status("exec-001")
        assert isinstance(status, WorkflowExecution)
        assert status.execution_id == "exec-001"
        assert status.status == StepStatus.RUNNING
        assert status.current_step == "step-2"

    @pytest.mark.asyncio
    async def test_cancel_returns_bool(self) -> None:
        """Test that cancel returns a boolean result."""

        class MockEngine(WorkflowEnginePort):
            async def create_workflow(self, definition: WorkflowDefinition) -> str:
                return "wf-1"

            async def execute(self, workflow_id: str, inputs: dict) -> str:
                return "exec-1"

            async def get_status(self, execution_id: str) -> WorkflowExecution:
                return WorkflowExecution(
                    execution_id=execution_id,
                    workflow_id="wf-1",
                    status=StepStatus.PENDING,
                )

            async def cancel(self, execution_id: str) -> bool:
                return True

            async def resume(self, execution_id: str, input_data: dict) -> bool:
                return True

        engine = MockEngine()
        result = await engine.cancel("exec-001")
        assert result is True

    @pytest.mark.asyncio
    async def test_resume_returns_bool(self) -> None:
        """Test that resume returns a boolean result."""

        class MockEngine(WorkflowEnginePort):
            async def create_workflow(self, definition: WorkflowDefinition) -> str:
                return "wf-1"

            async def execute(self, workflow_id: str, inputs: dict) -> str:
                return "exec-1"

            async def get_status(self, execution_id: str) -> WorkflowExecution:
                return WorkflowExecution(
                    execution_id=execution_id,
                    workflow_id="wf-1",
                    status=StepStatus.WAITING,
                )

            async def cancel(self, execution_id: str) -> bool:
                return True

            async def resume(self, execution_id: str, input_data: dict) -> bool:
                return True

        engine = MockEngine()
        result = await engine.resume("exec-001", {"approval": True})
        assert result is True
