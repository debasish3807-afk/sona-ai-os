"""Abstract port interfaces for the Workflow Engine service.

Defines the contracts that infrastructure adapters must implement
to provide workflow execution, management, and lifecycle capabilities.
"""

from abc import ABC, abstractmethod
from typing import Any

from sona_workflow.domain.models import WorkflowDefinition, WorkflowExecution


class WorkflowEnginePort(ABC):
    """Port for workflow execution and management.

    Provides the primary interface for creating, executing, monitoring,
    cancelling, and resuming multi-step workflows. Concrete adapters
    handle persistence, step execution, retry logic, and scheduling.
    """

    @abstractmethod
    async def create_workflow(self, definition: WorkflowDefinition) -> str:
        """Create a workflow definition.

        Persists the workflow definition and makes it available for
        execution. Validates step dependencies and conditions.

        Args:
            definition: The complete workflow definition to create.

        Returns:
            The workflow_id of the created workflow.
        """
        ...

    @abstractmethod
    async def execute(self, workflow_id: str, inputs: dict[str, Any]) -> str:
        """Start workflow execution.

        Begins executing the specified workflow with the given inputs.
        Steps are executed in dependency order with retry and timeout
        handling.

        Args:
            workflow_id: The identifier of the workflow definition to execute.
            inputs: Input parameters for the workflow execution.

        Returns:
            The execution_id of the started execution.
        """
        ...

    @abstractmethod
    async def get_status(self, execution_id: str) -> WorkflowExecution:
        """Get current workflow execution status.

        Retrieves the full execution state including current step,
        step results, and timing information.

        Args:
            execution_id: The identifier of the execution to query.

        Returns:
            A WorkflowExecution with current state information.
        """
        ...

    @abstractmethod
    async def cancel(self, execution_id: str) -> bool:
        """Cancel a running workflow.

        Attempts to stop execution of the specified workflow. Running
        steps may be allowed to complete or forcibly terminated depending
        on implementation.

        Args:
            execution_id: The identifier of the execution to cancel.

        Returns:
            True if cancellation was successful, False otherwise.
        """
        ...

    @abstractmethod
    async def resume(self, execution_id: str, input_data: dict[str, Any]) -> bool:
        """Resume a workflow waiting for human input.

        Provides the requested input data to a workflow that is in
        the WAITING state, allowing execution to continue from the
        paused step.

        Args:
            execution_id: The identifier of the execution to resume.
            input_data: The input data to provide to the waiting step.

        Returns:
            True if the workflow was successfully resumed, False otherwise.
        """
        ...
