"""DAG-based workflow executor with parallel layer execution."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from config.logging import get_logger
from runtime.schemas import TaskState, Workflow, WorkflowTask
from runtime.task_queue import TaskQueue
from runtime.worker_pool import WorkerPool
from runtime.workflow_graph import WorkflowGraph

logger = get_logger(__name__)


class DAGExecutor:
    """Executes workflows following DAG dependency ordering."""

    def __init__(self) -> None:
        self._execution_log: list[dict[str, Any]] = []

    async def execute_workflow(
        self,
        workflow: Workflow,
        graph: WorkflowGraph,
        pool: WorkerPool,
        queue: TaskQueue,
    ) -> Workflow:
        """Execute a workflow by processing layers in order."""
        layers = graph.get_execution_layers()
        for layer in layers:
            layer_tasks = [
                graph._tasks[tid]
                for tid in layer
                if tid in graph._tasks and graph._tasks[tid].state == TaskState.PENDING
            ]
            if layer_tasks:
                completed_tasks = await self._execute_layer(layer_tasks, pool, queue)
                for task in completed_tasks:
                    if task.state == TaskState.COMPLETED:
                        graph.mark_completed(task.task_id, task.result)
                    elif task.state == TaskState.FAILED:
                        graph.mark_failed(task.task_id, task.result.get("error", "unknown"))

        return workflow

    async def _execute_task(self, task: WorkflowTask, worker: Any) -> WorkflowTask:
        """Execute a single task (simulated execution)."""
        start_time = time.time()
        task.state = TaskState.RUNNING
        self._execution_log.append(
            {
                "task_id": task.task_id,
                "name": task.name,
                "event": "started",
                "timestamp": start_time,
            }
        )

        await asyncio.sleep(0)

        task.state = TaskState.COMPLETED
        task.result = {"status": "success", "output": f"{task.name}_result"}
        task.duration_ms = (time.time() - start_time) * 1000

        self._execution_log.append(
            {
                "task_id": task.task_id,
                "name": task.name,
                "event": "completed",
                "duration_ms": task.duration_ms,
                "timestamp": time.time(),
            }
        )
        return task

    async def _execute_layer(
        self,
        tasks: list[WorkflowTask],
        pool: WorkerPool,
        queue: TaskQueue,
    ) -> list[WorkflowTask]:
        """Execute a layer of tasks concurrently."""
        results: list[WorkflowTask] = []
        coros = []

        for task in tasks:
            worker = pool.allocate(task)
            if worker:
                coros.append(self._execute_task(task, worker))
            else:
                queue.enqueue(task)
                task.state = TaskState.QUEUED
                results.append(task)

        if coros:
            completed = await asyncio.gather(*coros)
            results.extend(completed)

        for task in results:
            if task.state == TaskState.COMPLETED:
                for w in pool.get_busy():
                    if w.current_task == task.task_id:
                        pool.release(w.worker_id)
                        break

        return results

    def _should_retry(self, task: WorkflowTask) -> bool:
        """Determine if a failed task should be retried."""
        return task.retry_count < task.max_retries

    def get_execution_log(self) -> list[dict[str, Any]]:
        """Return the execution log."""
        return list(self._execution_log)
