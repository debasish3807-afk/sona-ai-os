"""Main Runtime Engine — orchestrates all workflow subsystems."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger
from runtime.checkpoint_manager import CheckpointManager
from runtime.dag_executor import DAGExecutor
from runtime.events import RuntimeEvent, RuntimeEventType
from runtime.recovery_manager import RecoveryManager
from runtime.retry_manager import RetryManager
from runtime.rollback_manager import RollbackManager
from runtime.schemas import (
    TaskState,
    Workflow,
    WorkflowState,
)
from runtime.task_queue import TaskQueue
from runtime.telemetry import RuntimeTelemetry
from runtime.worker_pool import WorkerPool
from runtime.workflow_graph import WorkflowGraph
from runtime.workflow_monitor import WorkflowMonitor
from runtime.workflow_policies import PolicyEngine, WorkflowPolicies
from runtime.workflow_scheduler import WorkflowScheduler

logger = get_logger(__name__)


class RuntimeEngine:
    """Central orchestrator for the Runtime & Autonomous Workflow Engine."""

    def __init__(
        self,
        scheduler: WorkflowScheduler | None = None,
        queue: TaskQueue | None = None,
        pool: WorkerPool | None = None,
        dag_executor: DAGExecutor | None = None,
        checkpoint_mgr: CheckpointManager | None = None,
        retry_mgr: RetryManager | None = None,
        rollback_mgr: RollbackManager | None = None,
        recovery_mgr: RecoveryManager | None = None,
        monitor: WorkflowMonitor | None = None,
        policies: WorkflowPolicies | None = None,
    ) -> None:
        self._scheduler = scheduler or WorkflowScheduler()
        self._queue = queue or TaskQueue()
        self._pool = pool or WorkerPool()
        self._dag_executor = dag_executor or DAGExecutor()
        self._checkpoint_mgr = checkpoint_mgr or CheckpointManager()
        self._retry_mgr = retry_mgr or RetryManager()
        self._rollback_mgr = rollback_mgr or RollbackManager()
        self._recovery_mgr = recovery_mgr or RecoveryManager()
        self._monitor = monitor or WorkflowMonitor()
        self._policies = policies or WorkflowPolicies()
        self._policy_engine = PolicyEngine()
        self._telemetry = RuntimeTelemetry()
        self._workflows: dict[str, Workflow] = {}
        self._events: list[RuntimeEvent] = []

    async def submit_workflow(self, workflow: Workflow) -> str:
        """Submit a workflow for execution and return its ID."""
        self._workflows[workflow.workflow_id] = workflow
        self._scheduler.schedule(workflow)
        self._emit(
            RuntimeEventType.WORKFLOW_CREATED,
            workflow.workflow_id,
            {
                "name": workflow.name,
                "tasks": len(workflow.tasks),
            },
        )
        logger.info("workflow_submitted", workflow_id=workflow.workflow_id)
        return workflow.workflow_id

    async def execute(self, workflow: Workflow) -> Workflow:
        """Execute a workflow to completion."""
        self._workflows[workflow.workflow_id] = workflow
        workflow.state = WorkflowState.RUNNING
        workflow.started_at = time.time()
        self._monitor.record_start(workflow.workflow_id)
        self._emit(RuntimeEventType.WORKFLOW_STARTED, workflow.workflow_id, {})

        graph = WorkflowGraph()
        for task in workflow.tasks:
            graph.add_task(task)

        await self._dag_executor.execute_workflow(workflow, graph, self._pool, self._queue)

        all_completed = all(t.state == TaskState.COMPLETED for t in workflow.tasks)
        if all_completed:
            workflow.state = WorkflowState.COMPLETED
        else:
            has_failed = any(t.state == TaskState.FAILED for t in workflow.tasks)
            if has_failed:
                workflow.state = WorkflowState.FAILED
            else:
                workflow.state = WorkflowState.COMPLETED

        workflow.completed_at = time.time()
        workflow.total_duration_ms = (workflow.completed_at - workflow.started_at) * 1000
        self._monitor.record_complete(workflow.workflow_id, workflow.total_duration_ms)
        self._emit(
            RuntimeEventType.WORKFLOW_COMPLETED,
            workflow.workflow_id,
            {
                "duration_ms": workflow.total_duration_ms,
                "state": workflow.state.value,
            },
        )
        return workflow

    async def pause(self, workflow_id: str) -> bool:
        """Pause a running workflow."""
        workflow = self._workflows.get(workflow_id)
        if workflow is None or workflow.state != WorkflowState.RUNNING:
            return False
        workflow.state = WorkflowState.PAUSED
        self._checkpoint_mgr.create(workflow_id, workflow.to_dict())
        self._emit(RuntimeEventType.WORKFLOW_PAUSED, workflow_id, {})
        logger.info("workflow_paused", workflow_id=workflow_id)
        return True

    async def resume(self, workflow_id: str) -> bool:
        """Resume a paused workflow."""
        workflow = self._workflows.get(workflow_id)
        if workflow is None or workflow.state != WorkflowState.PAUSED:
            return False
        workflow.state = WorkflowState.RUNNING
        self._emit(RuntimeEventType.WORKFLOW_RESUMED, workflow_id, {})
        logger.info("workflow_resumed", workflow_id=workflow_id)
        return True

    async def cancel(self, workflow_id: str) -> bool:
        """Cancel a workflow."""
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            return False
        if workflow.state in (WorkflowState.COMPLETED, WorkflowState.CANCELLED):
            return False
        workflow.state = WorkflowState.CANCELLED
        workflow.completed_at = time.time()
        self._emit(RuntimeEventType.WORKFLOW_CANCELLED, workflow_id, {})
        logger.info("workflow_cancelled", workflow_id=workflow_id)
        return True

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        """Get a workflow by ID."""
        return self._workflows.get(workflow_id)

    def list_workflows(self, state: WorkflowState | None = None) -> list[Workflow]:
        """List workflows, optionally filtered by state."""
        workflows = list(self._workflows.values())
        if state is not None:
            workflows = [w for w in workflows if w.state == state]
        return workflows

    def get_status(self) -> dict[str, Any]:
        """Return the overall runtime engine status."""
        return {
            "total_workflows": len(self._workflows),
            "scheduler": self._scheduler.get_stats(),
            "queue": self._queue.get_stats(),
            "pool": self._pool.get_stats(),
            "monitor": self._monitor.get_summary(),
            "events_count": len(self._events),
        }

    def _emit(
        self,
        event_type: RuntimeEventType,
        workflow_id: str,
        data: dict[str, Any],
    ) -> None:
        """Emit a runtime event."""
        event = RuntimeEvent(
            event_type=event_type,
            workflow_id=workflow_id,
            data=data,
        )
        self._events.append(event)
