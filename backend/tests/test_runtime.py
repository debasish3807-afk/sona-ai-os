"""Comprehensive tests for the Runtime & Autonomous Workflow Engine."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

sys.path.insert(0, "/projects/sandbox/sona-ai-os/backend")


from runtime.checkpoint_manager import CheckpointManager
from runtime.dag_executor import DAGExecutor
from runtime.events import RuntimeEvent, RuntimeEventType
from runtime.exceptions import (
    CheckpointError,
    RecoveryError,
    RuntimeEngineError,
    WorkflowError,
)
from runtime.recovery_manager import RecoveryManager
from runtime.retry_manager import RetryManager
from runtime.rollback_manager import RollbackManager
from runtime.runtime_engine import RuntimeEngine
from runtime.schemas import (
    QueuePriority,
    TaskState,
    WorkerInfo,
    WorkerState,
    WorkerType,
    Workflow,
    WorkflowState,
    WorkflowTask,
    WorkflowType,
)
from runtime.task_queue import TaskQueue
from runtime.telemetry import RuntimeTelemetry
from runtime.worker_pool import WorkerPool
from runtime.workflow_graph import WorkflowGraph
from runtime.workflow_monitor import WorkflowMonitor
from runtime.workflow_policies import PolicyEngine, WorkflowPolicies
from runtime.workflow_scheduler import WorkflowScheduler

# ──────────────────────────────────────────────────────────────
# Helper factories
# ──────────────────────────────────────────────────────────────


def _make_task(name: str = "task1", **kwargs: Any) -> WorkflowTask:
    return WorkflowTask(name=name, capability_id="cap1", **kwargs)


def _make_workflow(
    name: str = "test-wf", tasks: list[WorkflowTask] | None = None, **kwargs: Any
) -> Workflow:
    return Workflow(name=name, tasks=tasks or [], **kwargs)


# ──────────────────────────────────────────────────────────────
# TestSchemas
# ──────────────────────────────────────────────────────────────


class TestSchemas:
    """Tests for schema dataclasses and enums."""

    def test_workflow_state_values(self) -> None:
        assert WorkflowState.CREATED.value == "created"
        assert WorkflowState.RUNNING.value == "running"
        assert WorkflowState.COMPLETED.value == "completed"
        assert len(WorkflowState) == 13

    def test_workflow_type_values(self) -> None:
        assert WorkflowType.SEQUENTIAL.value == "sequential"
        assert WorkflowType.PARALLEL.value == "parallel"
        assert len(WorkflowType) == 14

    def test_task_state_values(self) -> None:
        assert TaskState.PENDING.value == "pending"
        assert TaskState.COMPLETED.value == "completed"
        assert len(TaskState) == 8

    def test_worker_type_values(self) -> None:
        assert WorkerType.CPU.value == "cpu"
        assert WorkerType.GPU.value == "gpu"
        assert len(WorkerType) == 8

    def test_queue_priority_ordering(self) -> None:
        assert QueuePriority.CRITICAL < QueuePriority.HIGH
        assert QueuePriority.HIGH < QueuePriority.NORMAL
        assert QueuePriority.NORMAL < QueuePriority.LOW
        assert QueuePriority.LOW < QueuePriority.BACKGROUND

    def test_workflow_task_creation(self) -> None:
        task = _make_task(name="test-task", params={"key": "val"})
        assert task.name == "test-task"
        assert task.capability_id == "cap1"
        assert task.state == TaskState.PENDING
        assert task.params == {"key": "val"}
        assert task.retry_count == 0

    def test_workflow_task_to_dict(self) -> None:
        task = _make_task()
        d = task.to_dict()
        assert d["name"] == "task1"
        assert d["state"] == "pending"
        assert "task_id" in d
        assert isinstance(d, dict)

    def test_workflow_creation(self) -> None:
        wf = _make_workflow(name="wf1")
        assert wf.name == "wf1"
        assert wf.state == WorkflowState.CREATED
        assert wf.workflow_type == WorkflowType.SEQUENTIAL
        assert wf.tasks == []
        assert wf.created_at > 0

    def test_workflow_to_dict(self) -> None:
        task = _make_task()
        wf = _make_workflow(tasks=[task])
        d = wf.to_dict()
        assert d["name"] == "test-wf"
        assert d["state"] == "created"
        assert len(d["tasks"]) == 1
        assert isinstance(d, dict)

    def test_worker_info_creation(self) -> None:
        worker = WorkerInfo(worker_type=WorkerType.IO)
        assert worker.worker_type == WorkerType.IO
        assert worker.state == WorkerState.CREATED
        assert worker.current_task == ""
        assert worker.tasks_completed == 0

    def test_worker_info_to_dict(self) -> None:
        worker = WorkerInfo()
        d = worker.to_dict()
        assert d["worker_type"] == "cpu"
        assert d["state"] == "created"
        assert isinstance(d, dict)


# ──────────────────────────────────────────────────────────────
# TestWorkflowGraph
# ──────────────────────────────────────────────────────────────


class TestWorkflowGraph:
    """Tests for WorkflowGraph DAG operations."""

    def test_add_task(self) -> None:
        graph = WorkflowGraph()
        task = _make_task()
        tid = graph.add_task(task)
        assert tid == task.task_id
        assert task.task_id in graph._tasks

    def test_add_dependency(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        t2 = _make_task(name="t2")
        graph.add_task(t1)
        graph.add_task(t2)
        graph.add_dependency(t2.task_id, t1.task_id)
        assert t1.task_id in t2.dependencies

    def test_get_ready_tasks(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        t2 = _make_task(name="t2", dependencies=[t1.task_id])
        graph.add_task(t1)
        graph.add_task(t2)
        ready = graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == t1.task_id

    def test_execution_layers(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        t2 = _make_task(name="t2")
        t3 = _make_task(name="t3", dependencies=[t1.task_id, t2.task_id])
        graph.add_task(t1)
        graph.add_task(t2)
        graph.add_task(t3)
        layers = graph.get_execution_layers()
        assert len(layers) == 2
        assert t1.task_id in layers[0]
        assert t2.task_id in layers[0]
        assert t3.task_id in layers[1]

    def test_topological_sort(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        t2 = _make_task(name="t2", dependencies=[t1.task_id])
        graph.add_task(t1)
        graph.add_task(t2)
        order = graph.topological_sort()
        assert order.index(t1.task_id) < order.index(t2.task_id)

    def test_has_cycle_no_cycle(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        t2 = _make_task(name="t2", dependencies=[t1.task_id])
        graph.add_task(t1)
        graph.add_task(t2)
        assert graph.has_cycle() is False

    def test_critical_path(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        t2 = _make_task(name="t2", dependencies=[t1.task_id])
        graph.add_task(t1)
        graph.add_task(t2)
        path = graph.get_critical_path()
        assert len(path) >= 1

    def test_mark_completed(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        graph.add_task(t1)
        graph.mark_completed(t1.task_id, {"output": "done"})
        assert graph._tasks[t1.task_id].state == TaskState.COMPLETED
        assert graph._tasks[t1.task_id].result == {"output": "done"}

    def test_mark_failed(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        graph.add_task(t1)
        graph.mark_failed(t1.task_id, "timeout")
        assert graph._tasks[t1.task_id].state == TaskState.FAILED
        assert graph._tasks[t1.task_id].result == {"error": "timeout"}

    def test_progress(self) -> None:
        graph = WorkflowGraph()
        t1 = _make_task(name="t1")
        t2 = _make_task(name="t2")
        graph.add_task(t1)
        graph.add_task(t2)
        assert graph.get_progress() == 0.0
        graph.mark_completed(t1.task_id, {})
        assert graph.get_progress() == 0.5
        graph.mark_completed(t2.task_id, {})
        assert graph.get_progress() == 1.0


# ──────────────────────────────────────────────────────────────
# TestTaskQueue
# ──────────────────────────────────────────────────────────────


class TestTaskQueue:
    """Tests for priority task queue."""

    def test_enqueue(self) -> None:
        q = TaskQueue()
        task = _make_task()
        q.enqueue(task)
        assert q.size() == 1

    def test_dequeue_priority_ordering(self) -> None:
        q = TaskQueue()
        low = _make_task(name="low", priority=QueuePriority.LOW)
        high = _make_task(name="high", priority=QueuePriority.HIGH)
        q.enqueue(low)
        q.enqueue(high)
        result = q.dequeue()
        assert result is not None
        assert result.name == "high"

    def test_peek(self) -> None:
        q = TaskQueue()
        task = _make_task()
        q.enqueue(task)
        peeked = q.peek()
        assert peeked is not None
        assert peeked.task_id == task.task_id
        assert q.size() == 1

    def test_size(self) -> None:
        q = TaskQueue()
        assert q.size() == 0
        q.enqueue(_make_task(name="a"))
        q.enqueue(_make_task(name="b"))
        assert q.size() == 2

    def test_is_empty(self) -> None:
        q = TaskQueue()
        assert q.is_empty() is True
        q.enqueue(_make_task())
        assert q.is_empty() is False

    def test_dead_letter(self) -> None:
        q = TaskQueue()
        task = _make_task()
        q.move_to_dead_letter(task, "max retries exceeded")
        dls = q.get_dead_letters()
        assert len(dls) == 1
        assert dls[0].task_id == task.task_id

    def test_clear_dead_letters(self) -> None:
        q = TaskQueue()
        q.move_to_dead_letter(_make_task(), "err")
        q.move_to_dead_letter(_make_task(name="t2"), "err2")
        count = q.clear_dead_letters()
        assert count == 2
        assert len(q.get_dead_letters()) == 0

    def test_stats(self) -> None:
        q = TaskQueue()
        q.enqueue(_make_task(priority=QueuePriority.HIGH))
        q.enqueue(_make_task(name="t2", priority=QueuePriority.LOW))
        stats = q.get_stats()
        assert stats["total_size"] == 2
        assert stats["size_by_priority"]["HIGH"] == 1
        assert stats["size_by_priority"]["LOW"] == 1

    def test_fifo_within_priority(self) -> None:
        q = TaskQueue()
        t1 = _make_task(name="first")
        t2 = _make_task(name="second")
        q.enqueue(t1)
        q.enqueue(t2)
        result = q.dequeue()
        assert result is not None
        assert result.name == "first"

    def test_multiple_priorities(self) -> None:
        q = TaskQueue()
        q.enqueue(_make_task(name="bg", priority=QueuePriority.BACKGROUND))
        q.enqueue(_make_task(name="crit", priority=QueuePriority.CRITICAL))
        q.enqueue(_make_task(name="norm", priority=QueuePriority.NORMAL))
        first = q.dequeue()
        assert first is not None
        assert first.name == "crit"
        second = q.dequeue()
        assert second is not None
        assert second.name == "norm"
        third = q.dequeue()
        assert third is not None
        assert third.name == "bg"


# ──────────────────────────────────────────────────────────────
# TestWorkerPool
# ──────────────────────────────────────────────────────────────


class TestWorkerPool:
    """Tests for worker pool management."""

    def test_create_worker(self) -> None:
        pool = WorkerPool()
        worker = pool.create_worker(WorkerType.IO)
        assert worker.worker_type == WorkerType.IO
        assert worker.state == WorkerState.CREATED

    def test_allocate(self) -> None:
        pool = WorkerPool()
        pool.create_worker()
        task = _make_task()
        worker = pool.allocate(task)
        assert worker is not None
        assert worker.state == WorkerState.ALLOCATED
        assert worker.current_task == task.task_id

    def test_release(self) -> None:
        pool = WorkerPool()
        w = pool.create_worker()
        task = _make_task()
        pool.allocate(task)
        assert pool.release(w.worker_id) is True
        assert w.state == WorkerState.CREATED
        assert w.tasks_completed == 1

    def test_get_available(self) -> None:
        pool = WorkerPool()
        pool.create_worker()
        pool.create_worker()
        assert len(pool.get_available()) == 2

    def test_get_busy(self) -> None:
        pool = WorkerPool()
        pool.create_worker()
        task = _make_task()
        pool.allocate(task)
        assert len(pool.get_busy()) == 1

    def test_shutdown_worker(self) -> None:
        pool = WorkerPool()
        w = pool.create_worker()
        assert pool.shutdown_worker(w.worker_id) is True
        assert w.state == WorkerState.SHUTDOWN

    def test_drain_all(self) -> None:
        pool = WorkerPool()
        pool.create_worker()
        pool.create_worker()
        count = pool.drain_all()
        assert count == 2

    def test_utilization(self) -> None:
        pool = WorkerPool()
        pool.create_worker()
        assert pool.get_utilization() == 0.0
        pool.allocate(_make_task())
        assert pool.get_utilization() == 1.0

    def test_resize(self) -> None:
        pool = WorkerPool(max_workers=4)
        pool.resize(8)
        assert pool._max_workers == 8
        pool.resize(0)
        assert pool._max_workers == 1

    def test_stats(self) -> None:
        pool = WorkerPool(max_workers=4)
        pool.create_worker()
        stats = pool.get_stats()
        assert stats["total_workers"] == 1
        assert stats["max_workers"] == 4
        assert stats["available"] == 1
        assert stats["busy"] == 0


# ──────────────────────────────────────────────────────────────
# TestDAGExecutor
# ──────────────────────────────────────────────────────────────


class TestDAGExecutor:
    """Tests for DAG-based workflow execution."""

    def test_execute_sequential(self) -> None:
        executor = DAGExecutor()
        t1 = _make_task(name="s1")
        t2 = _make_task(name="s2", dependencies=[t1.task_id])
        wf = _make_workflow(tasks=[t1, t2])
        graph = WorkflowGraph()
        graph.add_task(t1)
        graph.add_task(t2)
        pool = WorkerPool()
        queue = TaskQueue()
        result = asyncio.run(executor.execute_workflow(wf, graph, pool, queue))
        assert result is wf

    def test_execute_parallel(self) -> None:
        executor = DAGExecutor()
        t1 = _make_task(name="p1")
        t2 = _make_task(name="p2")
        wf = _make_workflow(tasks=[t1, t2])
        graph = WorkflowGraph()
        graph.add_task(t1)
        graph.add_task(t2)
        pool = WorkerPool()
        queue = TaskQueue()
        asyncio.run(executor.execute_workflow(wf, graph, pool, queue))
        assert t1.state == TaskState.COMPLETED
        assert t2.state == TaskState.COMPLETED

    def test_task_completion(self) -> None:
        executor = DAGExecutor()
        t1 = _make_task(name="single")
        wf = _make_workflow(tasks=[t1])
        graph = WorkflowGraph()
        graph.add_task(t1)
        pool = WorkerPool()
        queue = TaskQueue()
        asyncio.run(executor.execute_workflow(wf, graph, pool, queue))
        assert t1.state == TaskState.COMPLETED
        assert "output" in t1.result

    def test_execution_log(self) -> None:
        executor = DAGExecutor()
        t1 = _make_task(name="logged")
        wf = _make_workflow(tasks=[t1])
        graph = WorkflowGraph()
        graph.add_task(t1)
        pool = WorkerPool()
        queue = TaskQueue()
        asyncio.run(executor.execute_workflow(wf, graph, pool, queue))
        log = executor.get_execution_log()
        assert len(log) >= 1

    def test_empty_workflow(self) -> None:
        executor = DAGExecutor()
        wf = _make_workflow(tasks=[])
        graph = WorkflowGraph()
        pool = WorkerPool()
        queue = TaskQueue()
        result = asyncio.run(executor.execute_workflow(wf, graph, pool, queue))
        assert result is wf

    def test_single_task(self) -> None:
        executor = DAGExecutor()
        t1 = _make_task(name="solo")
        wf = _make_workflow(tasks=[t1])
        graph = WorkflowGraph()
        graph.add_task(t1)
        pool = WorkerPool()
        queue = TaskQueue()
        asyncio.run(executor.execute_workflow(wf, graph, pool, queue))
        assert t1.state == TaskState.COMPLETED

    def test_multi_layer(self) -> None:
        executor = DAGExecutor()
        t1 = _make_task(name="layer1a")
        t2 = _make_task(name="layer1b")
        t3 = _make_task(name="layer2", dependencies=[t1.task_id, t2.task_id])
        wf = _make_workflow(tasks=[t1, t2, t3])
        graph = WorkflowGraph()
        graph.add_task(t1)
        graph.add_task(t2)
        graph.add_task(t3)
        pool = WorkerPool()
        queue = TaskQueue()
        asyncio.run(executor.execute_workflow(wf, graph, pool, queue))
        assert t1.state == TaskState.COMPLETED
        assert t2.state == TaskState.COMPLETED
        assert t3.state == TaskState.COMPLETED

    def test_should_retry(self) -> None:
        executor = DAGExecutor()
        task = _make_task(max_retries=3)
        assert executor._should_retry(task) is True
        task.retry_count = 3
        assert executor._should_retry(task) is False

    def test_retry_on_failure_check(self) -> None:
        executor = DAGExecutor()
        task = _make_task(max_retries=2)
        task.retry_count = 1
        assert executor._should_retry(task) is True
        task.retry_count = 2
        assert executor._should_retry(task) is False


# ──────────────────────────────────────────────────────────────
# TestWorkflowScheduler
# ──────────────────────────────────────────────────────────────


class TestWorkflowScheduler:
    """Tests for workflow scheduling."""

    def test_schedule(self) -> None:
        sched = WorkflowScheduler()
        wf = _make_workflow()
        assert sched.schedule(wf) is True

    def test_get_next(self) -> None:
        sched = WorkflowScheduler()
        wf = _make_workflow()
        sched.schedule(wf)
        nxt = sched.get_next()
        assert nxt is not None
        assert nxt.workflow_id == wf.workflow_id

    def test_mark_running(self) -> None:
        sched = WorkflowScheduler()
        wf = _make_workflow()
        sched.schedule(wf)
        assert sched.mark_running(wf.workflow_id) is True
        assert wf.state == WorkflowState.RUNNING

    def test_mark_completed(self) -> None:
        sched = WorkflowScheduler()
        wf = _make_workflow()
        sched.schedule(wf)
        sched.mark_running(wf.workflow_id)
        assert sched.mark_completed(wf.workflow_id) is True
        assert wf.state == WorkflowState.COMPLETED

    def test_cancel(self) -> None:
        sched = WorkflowScheduler()
        wf = _make_workflow()
        sched.schedule(wf)
        assert sched.cancel(wf.workflow_id) is True
        assert wf.state == WorkflowState.CANCELLED

    def test_list_pending(self) -> None:
        sched = WorkflowScheduler()
        wf1 = _make_workflow(name="p1")
        wf2 = _make_workflow(name="p2")
        sched.schedule(wf1)
        sched.schedule(wf2)
        pending = sched.list_pending()
        assert len(pending) == 2

    def test_list_running(self) -> None:
        sched = WorkflowScheduler()
        wf = _make_workflow()
        sched.schedule(wf)
        sched.mark_running(wf.workflow_id)
        running = sched.list_running()
        assert len(running) == 1
        assert running[0].workflow_id == wf.workflow_id

    def test_max_concurrent(self) -> None:
        sched = WorkflowScheduler(max_concurrent=1)
        wf1 = _make_workflow(name="c1")
        wf2 = _make_workflow(name="c2")
        sched.schedule(wf1)
        sched.mark_running(wf1.workflow_id)
        sched.schedule(wf2)
        assert sched.get_next() is None


# ──────────────────────────────────────────────────────────────
# TestCheckpointManager
# ──────────────────────────────────────────────────────────────


class TestCheckpointManager:
    """Tests for checkpoint management."""

    def test_create(self) -> None:
        mgr = CheckpointManager()
        cp_id = mgr.create("wf1", {"step": 3})
        assert isinstance(cp_id, str)
        assert len(cp_id) > 0

    def test_load(self) -> None:
        mgr = CheckpointManager()
        cp_id = mgr.create("wf1", {"step": 5})
        state = mgr.load(cp_id)
        assert state == {"step": 5}

    def test_load_latest(self) -> None:
        mgr = CheckpointManager()
        mgr.create("wf1", {"step": 1})
        mgr.create("wf1", {"step": 2})
        state = mgr.load_latest("wf1")
        assert state == {"step": 2}

    def test_list_for_workflow(self) -> None:
        mgr = CheckpointManager()
        mgr.create("wf1", {"a": 1})
        mgr.create("wf1", {"a": 2})
        mgr.create("wf2", {"b": 1})
        ids = mgr.list_for_workflow("wf1")
        assert len(ids) == 2

    def test_delete(self) -> None:
        mgr = CheckpointManager()
        cp_id = mgr.create("wf1", {"x": 1})
        assert mgr.delete(cp_id) is True
        assert mgr.load(cp_id) is None

    def test_stats(self) -> None:
        mgr = CheckpointManager()
        mgr.create("wf1", {})
        mgr.create("wf2", {})
        stats = mgr.get_stats()
        assert stats["total_checkpoints"] == 2
        assert stats["workflows_with_checkpoints"] == 2

    def test_nonexistent(self) -> None:
        mgr = CheckpointManager()
        assert mgr.load("nonexistent") is None
        assert mgr.load_latest("nonexistent") is None


# ──────────────────────────────────────────────────────────────
# TestRetryManager
# ──────────────────────────────────────────────────────────────


class TestRetryManager:
    """Tests for retry management."""

    def test_should_retry(self) -> None:
        mgr = RetryManager()
        task = _make_task(max_retries=3)
        assert mgr.should_retry(task) is True
        task.retry_count = 3
        assert mgr.should_retry(task) is False

    def test_backoff_delay(self) -> None:
        mgr = RetryManager(base_delay=1.0)
        task = _make_task()
        task.retry_count = 0
        delay0 = mgr.get_delay(task)
        assert delay0 >= 1.0
        task.retry_count = 2
        delay2 = mgr.get_delay(task)
        assert delay2 > delay0

    def test_record_retry(self) -> None:
        mgr = RetryManager()
        task = _make_task()
        assert task.retry_count == 0
        mgr.record_retry(task)
        assert task.retry_count == 1
        mgr.record_retry(task)
        assert task.retry_count == 2

    def test_max_reached(self) -> None:
        mgr = RetryManager()
        task = _make_task(max_retries=1)
        mgr.record_retry(task)
        assert mgr.should_retry(task) is False

    def test_stats(self) -> None:
        mgr = RetryManager()
        task = _make_task()
        mgr.record_retry(task)
        stats = mgr.get_stats()
        assert stats["total_retries"] == 1
        assert task.task_id in stats["by_task"]


# ──────────────────────────────────────────────────────────────
# TestRollbackManager
# ──────────────────────────────────────────────────────────────


class TestRollbackManager:
    """Tests for rollback management."""

    def test_rollback(self) -> None:
        mgr = RollbackManager()
        t1 = _make_task(name="done")
        t1.state = TaskState.COMPLETED
        wf = _make_workflow(tasks=[t1])
        result = mgr.rollback(wf, None)
        assert result is True
        assert wf.state == WorkflowState.ROLLING_BACK

    def test_compensate(self) -> None:
        mgr = RollbackManager()
        t1 = _make_task()
        t1.state = TaskState.COMPLETED
        success = mgr._compensate_task(t1)
        assert success is True
        assert t1.state == TaskState.CANCELLED

    def test_history(self) -> None:
        mgr = RollbackManager()
        t1 = _make_task()
        t1.state = TaskState.COMPLETED
        wf = _make_workflow(tasks=[t1])
        mgr.rollback(wf, None)
        history = mgr.get_rollback_history()
        assert len(history) == 1
        assert history[0]["workflow_id"] == wf.workflow_id

    def test_can_rollback(self) -> None:
        mgr = RollbackManager()
        t1 = _make_task()
        t1.state = TaskState.COMPLETED
        wf = _make_workflow(tasks=[t1])
        assert mgr.can_rollback(wf) is True
        wf.state = WorkflowState.CANCELLED
        assert mgr.can_rollback(wf) is False

    def test_empty_workflow(self) -> None:
        mgr = RollbackManager()
        wf = _make_workflow(tasks=[])
        assert mgr.can_rollback(wf) is False


# ──────────────────────────────────────────────────────────────
# TestRecoveryManager
# ──────────────────────────────────────────────────────────────


class TestRecoveryManager:
    """Tests for recovery management."""

    def test_recover(self) -> None:
        mgr = RecoveryManager()
        cp_mgr = CheckpointManager()
        wf = _make_workflow()
        wf.state = WorkflowState.FAILED
        cp_mgr.create(wf.workflow_id, {"step": 2})
        result = mgr.recover(wf, cp_mgr)
        assert result is not None
        assert result.state == WorkflowState.READY

    def test_can_recover(self) -> None:
        mgr = RecoveryManager()
        wf = _make_workflow()
        wf.state = WorkflowState.FAILED
        assert mgr.can_recover(wf) is True
        wf.state = WorkflowState.COMPLETED
        assert mgr.can_recover(wf) is False

    def test_recovery_log(self) -> None:
        mgr = RecoveryManager()
        cp_mgr = CheckpointManager()
        wf = _make_workflow()
        wf.state = WorkflowState.FAILED
        cp_mgr.create(wf.workflow_id, {"x": 1})
        mgr.recover(wf, cp_mgr)
        log = mgr.get_recovery_log()
        assert len(log) == 1
        assert log[0]["success"] is True

    def test_no_checkpoint(self) -> None:
        mgr = RecoveryManager()
        cp_mgr = CheckpointManager()
        wf = _make_workflow()
        wf.state = WorkflowState.FAILED
        result = mgr.recover(wf, cp_mgr)
        assert result is None
        log = mgr.get_recovery_log()
        assert log[0]["success"] is False

    def test_failed_state_required(self) -> None:
        mgr = RecoveryManager()
        cp_mgr = CheckpointManager()
        wf = _make_workflow()
        wf.state = WorkflowState.RUNNING
        result = mgr.recover(wf, cp_mgr)
        assert result is None


# ──────────────────────────────────────────────────────────────
# TestWorkflowMonitor
# ──────────────────────────────────────────────────────────────


class TestWorkflowMonitor:
    """Tests for workflow monitoring."""

    def test_record_start(self) -> None:
        mon = WorkflowMonitor()
        mon.record_start("wf1")
        assert "wf1" in mon._metrics
        assert mon._total_workflows == 1

    def test_task_complete(self) -> None:
        mon = WorkflowMonitor()
        mon.record_start("wf1")
        mon.record_task_complete("wf1", "t1", 150.0)
        assert mon._metrics["wf1"]["tasks_completed"] == 1

    def test_task_failure(self) -> None:
        mon = WorkflowMonitor()
        mon.record_start("wf1")
        mon.record_task_failure("wf1", "t1", "timeout")
        assert mon._metrics["wf1"]["tasks_failed"] == 1

    def test_workflow_complete(self) -> None:
        mon = WorkflowMonitor()
        mon.record_start("wf1")
        mon.record_complete("wf1", 500.0)
        assert mon._metrics["wf1"]["total_duration_ms"] == 500.0

    def test_metrics(self) -> None:
        mon = WorkflowMonitor()
        mon.record_start("wf1")
        mon.record_task_complete("wf1", "t1", 100.0)
        metrics = mon.get_workflow_metrics("wf1")
        assert metrics["tasks_completed"] == 1
        assert 100.0 in metrics["task_durations"]

    def test_summary(self) -> None:
        mon = WorkflowMonitor()
        mon.record_start("wf1")
        mon.record_complete("wf1", 200.0)
        mon.record_start("wf2")
        mon.record_complete("wf2", 400.0)
        summary = mon.get_summary()
        assert summary["total_workflows"] == 2
        assert summary["avg_duration_ms"] == 300.0


# ──────────────────────────────────────────────────────────────
# TestPolicies
# ──────────────────────────────────────────────────────────────


class TestPolicies:
    """Tests for workflow policies."""

    def test_evaluate_valid(self) -> None:
        engine = PolicyEngine()
        policies = WorkflowPolicies()
        wf = _make_workflow(tasks=[_make_task()])
        result = engine.evaluate(wf, policies)
        assert result["compliant"] is True
        assert result["violations"] == []

    def test_timeout_violation(self) -> None:
        engine = PolicyEngine()
        policies = WorkflowPolicies(workflow_timeout_seconds=30.0)
        task = _make_task(timeout_seconds=60.0)
        wf = _make_workflow(tasks=[task])
        result = engine.evaluate(wf, policies)
        assert len(result["violations"]) > 0
        assert result["compliant"] is False

    def test_retry_policy(self) -> None:
        engine = PolicyEngine()
        policies = WorkflowPolicies(max_retries=2)
        task = _make_task()
        task.retry_count = 1
        assert engine.apply_retry_policy(task, policies) is True
        task.retry_count = 2
        assert engine.apply_retry_policy(task, policies) is False

    def test_parallel_limit_warning(self) -> None:
        engine = PolicyEngine()
        policies = WorkflowPolicies(max_parallel_tasks=2)
        tasks = [_make_task(name=f"t{i}") for i in range(25)]
        wf = _make_workflow(tasks=tasks)
        result = engine.evaluate(wf, policies)
        assert len(result["warnings"]) > 0

    def test_failure_threshold(self) -> None:
        engine = PolicyEngine()
        policies = WorkflowPolicies(failure_threshold=0.3)
        t1 = _make_task(name="ok")
        t2 = _make_task(name="fail1")
        t2.result = {"error": "boom"}
        t3 = _make_task(name="fail2")
        t3.result = {"error": "crash"}
        wf = _make_workflow(tasks=[t1, t2, t3])
        result = engine.evaluate(wf, policies)
        assert result["compliant"] is False


# ──────────────────────────────────────────────────────────────
# TestRuntimeEngine
# ──────────────────────────────────────────────────────────────


class TestRuntimeEngine:
    """Tests for the main RuntimeEngine."""

    def test_submit(self) -> None:
        engine = RuntimeEngine()
        wf = _make_workflow()
        wf_id = asyncio.run(engine.submit_workflow(wf))
        assert wf_id == wf.workflow_id
        assert wf.workflow_id in engine._workflows

    def test_execute_sequential(self) -> None:
        engine = RuntimeEngine()
        t1 = _make_task(name="s1")
        t2 = _make_task(name="s2", dependencies=[t1.task_id])
        wf = _make_workflow(tasks=[t1, t2])
        result = asyncio.run(engine.execute(wf))
        assert result.state in (WorkflowState.COMPLETED, WorkflowState.FAILED)

    def test_execute_parallel(self) -> None:
        engine = RuntimeEngine()
        t1 = _make_task(name="p1")
        t2 = _make_task(name="p2")
        wf = _make_workflow(tasks=[t1, t2], workflow_type=WorkflowType.PARALLEL)
        result = asyncio.run(engine.execute(wf))
        assert result.state == WorkflowState.COMPLETED
        assert t1.state == TaskState.COMPLETED
        assert t2.state == TaskState.COMPLETED

    def test_pause(self) -> None:
        engine = RuntimeEngine()
        wf = _make_workflow()
        wf.state = WorkflowState.RUNNING
        engine._workflows[wf.workflow_id] = wf
        result = asyncio.run(engine.pause(wf.workflow_id))
        assert result is True
        assert wf.state == WorkflowState.PAUSED

    def test_resume(self) -> None:
        engine = RuntimeEngine()
        wf = _make_workflow()
        wf.state = WorkflowState.PAUSED
        engine._workflows[wf.workflow_id] = wf
        result = asyncio.run(engine.resume(wf.workflow_id))
        assert result is True
        assert wf.state == WorkflowState.RUNNING

    def test_cancel(self) -> None:
        engine = RuntimeEngine()
        wf = _make_workflow()
        wf.state = WorkflowState.RUNNING
        engine._workflows[wf.workflow_id] = wf
        result = asyncio.run(engine.cancel(wf.workflow_id))
        assert result is True
        assert wf.state == WorkflowState.CANCELLED

    def test_get_workflow(self) -> None:
        engine = RuntimeEngine()
        wf = _make_workflow()
        asyncio.run(engine.submit_workflow(wf))
        found = engine.get_workflow(wf.workflow_id)
        assert found is not None
        assert found.name == wf.name

    def test_list_workflows(self) -> None:
        engine = RuntimeEngine()
        wf1 = _make_workflow(name="wf1")
        wf2 = _make_workflow(name="wf2")
        asyncio.run(engine.submit_workflow(wf1))
        asyncio.run(engine.submit_workflow(wf2))
        workflows = engine.list_workflows()
        assert len(workflows) == 2

    def test_events(self) -> None:
        engine = RuntimeEngine()
        wf = _make_workflow()
        asyncio.run(engine.submit_workflow(wf))
        assert len(engine._events) >= 1
        assert engine._events[0].event_type == RuntimeEventType.WORKFLOW_CREATED

    def test_status(self) -> None:
        engine = RuntimeEngine()
        status = engine.get_status()
        assert "total_workflows" in status
        assert "scheduler" in status
        assert "queue" in status
        assert "pool" in status

    def test_complete_lifecycle(self) -> None:
        engine = RuntimeEngine()
        t1 = _make_task(name="lifecycle")
        wf = _make_workflow(tasks=[t1])
        asyncio.run(engine.submit_workflow(wf))
        result = asyncio.run(engine.execute(wf))
        assert result.state == WorkflowState.COMPLETED
        assert result.total_duration_ms > 0

    def test_error_handling_cancel_completed(self) -> None:
        engine = RuntimeEngine()
        wf = _make_workflow()
        wf.state = WorkflowState.COMPLETED
        engine._workflows[wf.workflow_id] = wf
        result = asyncio.run(engine.cancel(wf.workflow_id))
        assert result is False

    def test_pause_non_running(self) -> None:
        engine = RuntimeEngine()
        wf = _make_workflow()
        wf.state = WorkflowState.CREATED
        engine._workflows[wf.workflow_id] = wf
        result = asyncio.run(engine.pause(wf.workflow_id))
        assert result is False


# ──────────────────────────────────────────────────────────────
# TestRuntimeEvents
# ──────────────────────────────────────────────────────────────


class TestRuntimeEvents:
    """Tests for runtime events."""

    def test_event_creation(self) -> None:
        event = RuntimeEvent(
            event_type=RuntimeEventType.WORKFLOW_CREATED,
            workflow_id="wf-123",
            data={"name": "test"},
        )
        assert event.event_type == RuntimeEventType.WORKFLOW_CREATED
        assert event.workflow_id == "wf-123"
        assert len(event.event_id) > 0

    def test_to_dict(self) -> None:
        event = RuntimeEvent(
            event_type=RuntimeEventType.TASK_COMPLETED,
            workflow_id="wf-1",
        )
        d = event.to_dict()
        assert d["event_type"] == "task_completed"
        assert d["workflow_id"] == "wf-1"
        assert isinstance(d, dict)

    def test_types_count(self) -> None:
        assert len(RuntimeEventType) == 20

    def test_workflow_id_field(self) -> None:
        event = RuntimeEvent(event_type=RuntimeEventType.WORKER_ALLOCATED)
        assert event.workflow_id == ""


# ──────────────────────────────────────────────────────────────
# TestTelemetry
# ──────────────────────────────────────────────────────────────


class TestTelemetry:
    """Tests for runtime telemetry."""

    def test_record(self) -> None:
        tel = RuntimeTelemetry()
        tel.record("latency", 42.5, "executor")
        assert len(tel._records) == 1
        assert tel._records[0]["metric"] == "latency"

    def test_summary(self) -> None:
        tel = RuntimeTelemetry()
        tel.record("latency", 10.0)
        tel.record("latency", 20.0)
        tel.record("throughput", 100.0)
        summary = tel.get_summary()
        assert summary["total_records"] == 3
        assert summary["metrics"]["latency"]["avg"] == 15.0
        assert summary["metrics"]["latency"]["min"] == 10.0
        assert summary["metrics"]["latency"]["max"] == 20.0

    def test_reset(self) -> None:
        tel = RuntimeTelemetry()
        tel.record("x", 1.0)
        tel.record("y", 2.0)
        tel.reset()
        assert len(tel._records) == 0
        summary = tel.get_summary()
        assert summary["total_records"] == 0


# ──────────────────────────────────────────────────────────────
# TestExceptions
# ──────────────────────────────────────────────────────────────


class TestExceptions:
    """Tests for custom exceptions."""

    def test_runtime_error(self) -> None:
        err = RuntimeEngineError("test failure", "engine")
        assert err.message == "test failure"
        assert err.component == "engine"
        assert "engine" in str(err)

    def test_workflow_error(self) -> None:
        err = WorkflowError("invalid graph")
        assert err.component == "workflow"
        assert "invalid graph" in str(err)

    def test_checkpoint_error(self) -> None:
        err = CheckpointError("disk full")
        assert err.component == "checkpoint"
        assert "disk full" in str(err)

    def test_recovery_error(self) -> None:
        err = RecoveryError("corrupted state")
        assert err.component == "recovery"
        assert "corrupted state" in str(err)
