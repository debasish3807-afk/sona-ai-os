"""Resource Scheduler — allocates and enforces resource budgets for processes."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger
from microkernel.schemas import MessagePriority, ResourceBudget

logger = get_logger(__name__)


@dataclass
class ResourceAllocation:
    """A resource allocation assigned to a process."""

    process_id: str
    budget: ResourceBudget
    priority: MessagePriority
    allocated_at: float
    expires_at: float
    allocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class ResourceScheduler:
    """Manages resource allocations across microkernel processes.

    Tracks total capacity, grants allocations based on priority,
    and enforces deadlines to reclaim expired budgets.
    """

    def __init__(self, total_budget: ResourceBudget | None = None) -> None:
        self._allocations: dict[str, ResourceAllocation] = {}
        self._total_budget: ResourceBudget = total_budget or ResourceBudget(
            cpu_percent=800.0,
            memory_mb=8192,
            gpu_percent=0.0,
            disk_mb=102400,
            network_mbps=1000.0,
            token_budget=10_000_000,
            timeout_seconds=3600.0,
        )

    def allocate(
        self,
        process_id: str,
        budget: ResourceBudget,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> ResourceAllocation | None:
        """Allocate resources for a process. Returns None if insufficient."""
        if not self.has_capacity(budget):
            logger.warning("insufficient_resources", process_id=process_id)
            return None

        now = time.time()
        allocation = ResourceAllocation(
            process_id=process_id,
            budget=budget,
            priority=priority,
            allocated_at=now,
            expires_at=now + budget.timeout_seconds,
        )
        self._allocations[allocation.allocation_id] = allocation
        logger.info(
            "resources_allocated", allocation_id=allocation.allocation_id, process_id=process_id
        )
        return allocation

    def release(self, allocation_id: str) -> bool:
        """Release an allocation and free its resources."""
        if allocation_id not in self._allocations:
            return False

        del self._allocations[allocation_id]
        logger.info("resources_released", allocation_id=allocation_id)
        return True

    def get_available(self) -> ResourceBudget:
        """Calculate the currently available resource budget."""
        used_cpu = sum(a.budget.cpu_percent for a in self._allocations.values())
        used_memory = sum(a.budget.memory_mb for a in self._allocations.values())
        used_gpu = sum(a.budget.gpu_percent for a in self._allocations.values())
        used_disk = sum(a.budget.disk_mb for a in self._allocations.values())
        used_network = sum(a.budget.network_mbps for a in self._allocations.values())
        used_tokens = sum(a.budget.token_budget for a in self._allocations.values())

        return ResourceBudget(
            cpu_percent=max(0.0, self._total_budget.cpu_percent - used_cpu),
            memory_mb=max(0, self._total_budget.memory_mb - used_memory),
            gpu_percent=max(0.0, self._total_budget.gpu_percent - used_gpu),
            disk_mb=max(0, self._total_budget.disk_mb - used_disk),
            network_mbps=max(0.0, self._total_budget.network_mbps - used_network),
            token_budget=max(0, self._total_budget.token_budget - used_tokens),
            timeout_seconds=self._total_budget.timeout_seconds,
        )

    def get_usage(self) -> dict[str, Any]:
        """Return resource usage as percentages."""
        available = self.get_available()
        total = self._total_budget

        def pct(used: float, total_val: float) -> float:
            if total_val == 0:
                return 0.0
            return round((1 - used / total_val) * 100, 2)

        return {
            "cpu_percent_used": pct(available.cpu_percent, total.cpu_percent),
            "memory_mb_used": pct(available.memory_mb, total.memory_mb),
            "gpu_percent_used": pct(available.gpu_percent, total.gpu_percent)
            if total.gpu_percent > 0
            else 0.0,
            "disk_mb_used": pct(available.disk_mb, total.disk_mb),
            "network_mbps_used": pct(available.network_mbps, total.network_mbps),
            "token_budget_used": pct(available.token_budget, total.token_budget),
            "allocation_count": len(self._allocations),
        }

    def has_capacity(self, budget: ResourceBudget) -> bool:
        """Check if the requested budget can be satisfied."""
        available = self.get_available()
        return (
            budget.cpu_percent <= available.cpu_percent
            and budget.memory_mb <= available.memory_mb
            and budget.gpu_percent <= available.gpu_percent
            and budget.disk_mb <= available.disk_mb
            and budget.network_mbps <= available.network_mbps
            and budget.token_budget <= available.token_budget
        )

    def list_allocations(self) -> list[ResourceAllocation]:
        """List all active allocations."""
        return list(self._allocations.values())

    def enforce_deadline(self, allocation_id: str) -> bool:
        """Release an allocation if it has expired."""
        allocation = self._allocations.get(allocation_id)
        if allocation is None:
            return False

        if time.time() >= allocation.expires_at:
            self.release(allocation_id)
            return True

        return False

    def cleanup_expired(self) -> int:
        """Release all expired allocations. Returns count released."""
        now = time.time()
        expired = [aid for aid, a in self._allocations.items() if now >= a.expires_at]
        for aid in expired:
            del self._allocations[aid]
        if expired:
            logger.info("expired_allocations_cleaned", count=len(expired))
        return len(expired)
