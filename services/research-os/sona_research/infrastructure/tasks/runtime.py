"""Tasks runtime for personal task management.

Provides task lifecycle management with status transitions,
priority ordering, and subtask relationships.
"""

import structlog

from sona_research.domain.events import TaskCreatedEvent
from sona_research.domain.personal_models import Task, TaskPriority, TaskStatus

logger = structlog.get_logger()

# Valid status transitions
_VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.DONE, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.DONE: set(),  # Terminal state
    TaskStatus.CANCELLED: set(),  # Terminal state
}

# Priority ordering (lower number = higher priority)
_PRIORITY_ORDER: dict[TaskPriority, int] = {
    TaskPriority.CRITICAL: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.MEDIUM: 2,
    TaskPriority.LOW: 3,
}


class InvalidTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""

    def __init__(self, current: TaskStatus, target: TaskStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition from '{current.value}' to '{target.value}'")


class TasksRuntime:
    """Runtime for managing personal tasks.

    Supports task creation, status transitions, priority ordering,
    parent/subtask relationships, and due date tracking.
    """

    def __init__(self) -> None:
        """Initialize the tasks runtime."""
        self._tasks: dict[str, Task] = {}
        self._events: list[TaskCreatedEvent] = []
        self._next_id: int = 1

    @property
    def events(self) -> list[TaskCreatedEvent]:
        """Access emitted events."""
        return self._events

    def _generate_id(self) -> str:
        """Generate a unique task ID."""
        task_id = f"task-{self._next_id:04d}"
        self._next_id += 1
        return task_id

    async def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee: str = "",
        due_date: str = "",
        tags: list[str] | None = None,
        parent_task: str = "",
    ) -> Task:
        """Create a new task.

        Args:
            title: Task title.
            description: Task description.
            priority: Task priority level.
            assignee: Person assigned to the task.
            due_date: Due date string.
            tags: Optional list of tags.
            parent_task: Optional parent task ID.

        Returns:
            The created Task instance.
        """
        task = Task(
            task_id=self._generate_id(),
            title=title,
            description=description,
            status=TaskStatus.TODO,
            priority=priority,
            assignee=assignee,
            due_date=due_date,
            tags=tags or [],
            parent_task=parent_task,
        )
        self._tasks[task.task_id] = task

        # If this is a subtask, update parent
        if parent_task and parent_task in self._tasks:
            parent = self._tasks[parent_task]
            new_subtasks = [*parent.subtasks, task.task_id]
            updated_parent = Task(
                task_id=parent.task_id,
                title=parent.title,
                description=parent.description,
                status=parent.status,
                priority=parent.priority,
                assignee=parent.assignee,
                due_date=parent.due_date,
                tags=parent.tags,
                parent_task=parent.parent_task,
                subtasks=new_subtasks,
            )
            self._tasks[parent_task] = updated_parent

        event = TaskCreatedEvent(
            task_id=task.task_id,
            title=title,
            priority=priority.value,
        )
        self._events.append(event)

        logger.info("tasks.created", task_id=task.task_id, title=title)
        return task

    async def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: The task identifier.

        Returns:
            The Task if found, None otherwise.
        """
        return self._tasks.get(task_id)

    async def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        assignee: str | None = None,
        due_date: str | None = None,
        tags: list[str] | None = None,
    ) -> Task | None:
        """Update task fields (not status - use transition methods).

        Args:
            task_id: The task identifier.
            title: New title (None to keep current).
            description: New description (None to keep current).
            assignee: New assignee (None to keep current).
            due_date: New due date (None to keep current).
            tags: New tags (None to keep current).

        Returns:
            The updated Task if found, None otherwise.
        """
        existing = self._tasks.get(task_id)
        if existing is None:
            return None

        updated = Task(
            task_id=existing.task_id,
            title=title if title is not None else existing.title,
            description=description if description is not None else existing.description,
            status=existing.status,
            priority=existing.priority,
            assignee=assignee if assignee is not None else existing.assignee,
            due_date=due_date if due_date is not None else existing.due_date,
            tags=tags if tags is not None else existing.tags,
            parent_task=existing.parent_task,
            subtasks=existing.subtasks,
        )
        self._tasks[task_id] = updated
        logger.info("tasks.updated", task_id=task_id)
        return updated

    async def transition_status(self, task_id: str, new_status: TaskStatus) -> Task:
        """Transition a task to a new status.

        Args:
            task_id: The task identifier.
            new_status: The target status.

        Returns:
            The updated Task.

        Raises:
            ValueError: If task not found.
            InvalidTransitionError: If the transition is not valid.
        """
        existing = self._tasks.get(task_id)
        if existing is None:
            raise ValueError(f"Task not found: {task_id}")

        valid_targets = _VALID_TRANSITIONS.get(existing.status, set())
        if new_status not in valid_targets:
            raise InvalidTransitionError(existing.status, new_status)

        updated = Task(
            task_id=existing.task_id,
            title=existing.title,
            description=existing.description,
            status=new_status,
            priority=existing.priority,
            assignee=existing.assignee,
            due_date=existing.due_date,
            tags=existing.tags,
            parent_task=existing.parent_task,
            subtasks=existing.subtasks,
        )
        self._tasks[task_id] = updated
        logger.info(
            "tasks.transitioned",
            task_id=task_id,
            from_status=existing.status.value,
            to_status=new_status.value,
        )
        return updated

    async def complete_task(self, task_id: str) -> Task:
        """Mark a task as done (convenience method).

        First transitions to IN_PROGRESS if TODO, then to DONE.

        Args:
            task_id: The task identifier.

        Returns:
            The completed Task.
        """
        existing = self._tasks.get(task_id)
        if existing is None:
            raise ValueError(f"Task not found: {task_id}")

        if existing.status == TaskStatus.TODO:
            await self.transition_status(task_id, TaskStatus.IN_PROGRESS)

        return await self.transition_status(task_id, TaskStatus.DONE)

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID.

        Args:
            task_id: The task identifier.

        Returns:
            True if the task was found and deleted.
        """
        if task_id in self._tasks:
            task = self._tasks[task_id]
            # Remove from parent's subtasks
            if task.parent_task and task.parent_task in self._tasks:
                parent = self._tasks[task.parent_task]
                new_subtasks = [s for s in parent.subtasks if s != task_id]
                updated_parent = Task(
                    task_id=parent.task_id,
                    title=parent.title,
                    description=parent.description,
                    status=parent.status,
                    priority=parent.priority,
                    assignee=parent.assignee,
                    due_date=parent.due_date,
                    tags=parent.tags,
                    parent_task=parent.parent_task,
                    subtasks=new_subtasks,
                )
                self._tasks[parent.parent_task] = updated_parent

            del self._tasks[task_id]
            logger.info("tasks.deleted", task_id=task_id)
            return True
        return False

    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee: str | None = None,
    ) -> list[Task]:
        """List tasks with optional filters.

        Args:
            status: Filter by status.
            priority: Filter by priority.
            assignee: Filter by assignee.

        Returns:
            List of matching tasks, ordered by priority.
        """
        tasks = list(self._tasks.values())

        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        if priority is not None:
            tasks = [t for t in tasks if t.priority == priority]
        if assignee is not None:
            tasks = [t for t in tasks if t.assignee == assignee]

        # Sort by priority (critical first)
        tasks.sort(key=lambda t: _PRIORITY_ORDER.get(t.priority, 99))
        return tasks

    async def get_subtasks(self, task_id: str) -> list[Task]:
        """Get all subtasks of a task.

        Args:
            task_id: The parent task identifier.

        Returns:
            List of subtask Task instances.
        """
        parent = self._tasks.get(task_id)
        if parent is None:
            return []

        return [self._tasks[st_id] for st_id in parent.subtasks if st_id in self._tasks]

    async def get_overdue_tasks(self, reference_date: str) -> list[Task]:
        """Get tasks that are overdue based on a reference date.

        Args:
            reference_date: ISO date string to compare against.

        Returns:
            List of overdue tasks (due_date < reference_date and not done/cancelled).
        """
        overdue: list[Task] = []
        for task in self._tasks.values():
            if (
                task.due_date
                and task.due_date < reference_date
                and task.status not in (TaskStatus.DONE, TaskStatus.CANCELLED)
            ):
                overdue.append(task)
        return overdue

    async def count(self, status: TaskStatus | None = None) -> int:
        """Get count of tasks.

        Args:
            status: Optional status filter.

        Returns:
            Count of matching tasks.
        """
        if status is None:
            return len(self._tasks)
        return sum(1 for t in self._tasks.values() if t.status == status)
