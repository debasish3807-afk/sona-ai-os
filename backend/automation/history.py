"""Automation history — workflow execution logs and storage."""

from __future__ import annotations

import time
import uuid

from automation.schemas import HistoryEntry, WorkflowStatus


class AutomationHistory:
    """Stores and retrieves workflow execution history."""

    def __init__(self) -> None:
        self._entries: dict[str, HistoryEntry] = {}
        self._max_entries = 1000

    def record_start(
        self, workflow_id: str, name: str = "", owner: str = "", steps_total: int = 0
    ) -> str:
        self._evict_if_needed()
        entry = HistoryEntry(
            entry_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            workflow_name=name,
            status=WorkflowStatus.RUNNING,
            started_at=time.time(),
            steps_total=steps_total,
            owner=owner,
        )
        self._entries[entry.entry_id] = entry
        return entry.entry_id

    def record_complete(
        self,
        entry_id: str,
        status: WorkflowStatus = WorkflowStatus.COMPLETED,
        error: str = "",
        steps_completed: int = 0,
    ) -> None:
        entry = self._entries.get(entry_id)
        if entry is None:
            return
        entry.status = status
        entry.completed_at = time.time()
        entry.duration_ms = (entry.completed_at - entry.started_at) * 1000
        entry.error = error
        entry.steps_completed = steps_completed

    def get_entry(self, entry_id: str) -> HistoryEntry | None:
        return self._entries.get(entry_id)

    def list_entries(
        self, limit: int = 50, status: str | None = None, owner: str | None = None
    ) -> list[HistoryEntry]:
        entries = list(self._entries.values())
        if status:
            try:
                s = WorkflowStatus(status)
                entries = [e for e in entries if e.status == s]
            except ValueError:
                pass
        if owner:
            entries = [e for e in entries if e.owner == owner]
        entries.sort(key=lambda e: e.started_at, reverse=True)
        return entries[:limit]

    def get_stats(self) -> dict[str, int]:
        total = len(self._entries)
        completed = sum(1 for e in self._entries.values() if e.status == WorkflowStatus.COMPLETED)
        failed = sum(1 for e in self._entries.values() if e.status == WorkflowStatus.FAILED)
        running = sum(1 for e in self._entries.values() if e.status == WorkflowStatus.RUNNING)
        return {"total": total, "completed": completed, "failed": failed, "running": running}

    def _evict_if_needed(self) -> None:
        while len(self._entries) >= self._max_entries:
            oldest = min(self._entries.keys(), key=lambda k: self._entries[k].started_at)
            del self._entries[oldest]
