"""Tests for tasks runtime."""

import pytest

from sona_research.domain.personal_models import TaskPriority, TaskStatus
from sona_research.infrastructure.tasks.runtime import (
    InvalidTransitionError,
    TasksRuntime,
)


@pytest.fixture
def runtime() -> TasksRuntime:
    return TasksRuntime()


class TestTasksCreate:
    @pytest.mark.asyncio
    async def test_create_task(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Do something")
        assert task.title == "Do something"
        assert task.task_id.startswith("task-")
        assert task.status == TaskStatus.TODO

    @pytest.mark.asyncio
    async def test_create_with_priority(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("High", priority=TaskPriority.HIGH)
        assert task.priority == TaskPriority.HIGH

    @pytest.mark.asyncio
    async def test_create_with_all_fields(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task(
            "Full",
            description="Desc",
            priority=TaskPriority.CRITICAL,
            assignee="dev1",
            due_date="2024-12-31",
            tags=["urgent"],
        )
        assert task.description == "Desc"
        assert task.assignee == "dev1"
        assert task.due_date == "2024-12-31"
        assert task.tags == ["urgent"]

    @pytest.mark.asyncio
    async def test_create_emits_event(self, runtime: TasksRuntime) -> None:
        await runtime.create_task("Event", priority=TaskPriority.HIGH)
        assert len(runtime.events) == 1
        assert runtime.events[0].priority == "high"

    @pytest.mark.asyncio
    async def test_unique_ids(self, runtime: TasksRuntime) -> None:
        t1 = await runtime.create_task("A")
        t2 = await runtime.create_task("B")
        assert t1.task_id != t2.task_id


class TestTasksTransitions:
    @pytest.mark.asyncio
    async def test_todo_to_in_progress(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        updated = await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        assert updated.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_in_progress_to_done(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        updated = await runtime.transition_status(task.task_id, TaskStatus.DONE)
        assert updated.status == TaskStatus.DONE

    @pytest.mark.asyncio
    async def test_in_progress_to_blocked(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        updated = await runtime.transition_status(task.task_id, TaskStatus.BLOCKED)
        assert updated.status == TaskStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_blocked_to_in_progress(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        await runtime.transition_status(task.task_id, TaskStatus.BLOCKED)
        updated = await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        assert updated.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_invalid_done_to_todo(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        await runtime.transition_status(task.task_id, TaskStatus.DONE)
        with pytest.raises(InvalidTransitionError):
            await runtime.transition_status(task.task_id, TaskStatus.TODO)

    @pytest.mark.asyncio
    async def test_invalid_todo_to_done(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        with pytest.raises(InvalidTransitionError):
            await runtime.transition_status(task.task_id, TaskStatus.DONE)

    @pytest.mark.asyncio
    async def test_invalid_todo_to_blocked(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        with pytest.raises(InvalidTransitionError):
            await runtime.transition_status(task.task_id, TaskStatus.BLOCKED)

    @pytest.mark.asyncio
    async def test_cancel_from_todo(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        updated = await runtime.transition_status(task.task_id, TaskStatus.CANCELLED)
        assert updated.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_from_in_progress(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        updated = await runtime.transition_status(task.task_id, TaskStatus.CANCELLED)
        assert updated.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_nonexistent_task_raises(self, runtime: TasksRuntime) -> None:
        with pytest.raises(ValueError):
            await runtime.transition_status("nonexistent", TaskStatus.DONE)


class TestTasksComplete:
    @pytest.mark.asyncio
    async def test_complete_from_todo(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        completed = await runtime.complete_task(task.task_id)
        assert completed.status == TaskStatus.DONE

    @pytest.mark.asyncio
    async def test_complete_from_in_progress(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        completed = await runtime.complete_task(task.task_id)
        assert completed.status == TaskStatus.DONE

    @pytest.mark.asyncio
    async def test_complete_nonexistent_raises(self, runtime: TasksRuntime) -> None:
        with pytest.raises(ValueError):
            await runtime.complete_task("nope")


class TestTasksList:
    @pytest.mark.asyncio
    async def test_list_all(self, runtime: TasksRuntime) -> None:
        await runtime.create_task("A")
        await runtime.create_task("B")
        tasks = await runtime.list_tasks()
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_list_by_status(self, runtime: TasksRuntime) -> None:
        t1 = await runtime.create_task("A")
        await runtime.create_task("B")
        await runtime.transition_status(t1.task_id, TaskStatus.IN_PROGRESS)
        tasks = await runtime.list_tasks(status=TaskStatus.TODO)
        assert len(tasks) == 1
        assert tasks[0].title == "B"

    @pytest.mark.asyncio
    async def test_list_by_priority(self, runtime: TasksRuntime) -> None:
        await runtime.create_task("Low", priority=TaskPriority.LOW)
        await runtime.create_task("High", priority=TaskPriority.HIGH)
        tasks = await runtime.list_tasks(priority=TaskPriority.HIGH)
        assert len(tasks) == 1
        assert tasks[0].title == "High"

    @pytest.mark.asyncio
    async def test_list_sorted_by_priority(self, runtime: TasksRuntime) -> None:
        await runtime.create_task("Low", priority=TaskPriority.LOW)
        await runtime.create_task("Critical", priority=TaskPriority.CRITICAL)
        await runtime.create_task("Medium", priority=TaskPriority.MEDIUM)
        tasks = await runtime.list_tasks()
        assert tasks[0].priority == TaskPriority.CRITICAL
        assert tasks[-1].priority == TaskPriority.LOW

    @pytest.mark.asyncio
    async def test_list_by_assignee(self, runtime: TasksRuntime) -> None:
        await runtime.create_task("A", assignee="alice")
        await runtime.create_task("B", assignee="bob")
        tasks = await runtime.list_tasks(assignee="alice")
        assert len(tasks) == 1


class TestTasksSubtasks:
    @pytest.mark.asyncio
    async def test_create_subtask(self, runtime: TasksRuntime) -> None:
        parent = await runtime.create_task("Parent")
        child = await runtime.create_task("Child", parent_task=parent.task_id)
        assert child.parent_task == parent.task_id
        # Verify parent has subtask reference
        updated_parent = await runtime.get_task(parent.task_id)
        assert updated_parent is not None
        assert child.task_id in updated_parent.subtasks

    @pytest.mark.asyncio
    async def test_get_subtasks(self, runtime: TasksRuntime) -> None:
        parent = await runtime.create_task("Parent")
        await runtime.create_task("Child 1", parent_task=parent.task_id)
        await runtime.create_task("Child 2", parent_task=parent.task_id)
        subtasks = await runtime.get_subtasks(parent.task_id)
        assert len(subtasks) == 2


class TestTasksOverdue:
    @pytest.mark.asyncio
    async def test_overdue_tasks(self, runtime: TasksRuntime) -> None:
        await runtime.create_task("Overdue", due_date="2024-01-01")
        await runtime.create_task("Future", due_date="2025-12-31")
        overdue = await runtime.get_overdue_tasks("2024-06-01")
        assert len(overdue) == 1
        assert overdue[0].title == "Overdue"

    @pytest.mark.asyncio
    async def test_done_tasks_not_overdue(self, runtime: TasksRuntime) -> None:
        t = await runtime.create_task("Done", due_date="2024-01-01")
        await runtime.complete_task(t.task_id)
        overdue = await runtime.get_overdue_tasks("2024-06-01")
        assert len(overdue) == 0
