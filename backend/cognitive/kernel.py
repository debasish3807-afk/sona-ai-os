"""Cognitive Kernel — the central pipeline orchestrator."""

from __future__ import annotations

import time
from typing import Any

from cognitive.engine_registry import EngineRegistry
from cognitive.event_bus import EventBus
from cognitive.exceptions import (
    BudgetExceededError,
    EngineError,
    FailureCategory,
    KernelError,
    PipelineError,
)
from cognitive.execution_context import ExecutionContext
from cognitive.kernel_events import EventType, KernelEvent
from cognitive.lifecycle import KernelState, can_transition
from cognitive.metrics import KernelMetrics
from cognitive.request_context import RequestContext
from cognitive.world_state import WorldState
from config.logging import get_logger

logger = get_logger(__name__)

PIPELINE_STAGES: list[str] = [
    "intent",
    "goal",
    "context",
    "thinking",
    "reasoning",
    "planning",
    "decision",
    "execution",
    "verification",
    "learning",
    "memory",
]


class CognitiveKernel:
    """The central orchestration runtime."""

    def __init__(
        self, registry: EngineRegistry | None = None, event_bus: EventBus | None = None
    ) -> None:
        self._registry = registry or EngineRegistry()
        self._events = event_bus or EventBus()
        self._metrics = KernelMetrics()
        self._world = WorldState()
        self._state = KernelState.STARTING
        self._active_requests: int = 0

    @property
    def state(self) -> KernelState:
        return self._state

    @property
    def registry(self) -> EngineRegistry:
        return self._registry

    @property
    def event_bus(self) -> EventBus:
        return self._events

    @property
    def metrics(self) -> KernelMetrics:
        return self._metrics

    @property
    def world(self) -> WorldState:
        return self._world

    def _transition(self, target: KernelState) -> None:
        if not can_transition(self._state, target):
            raise PipelineError(f"Invalid transition: {self._state.value} -> {target.value}")
        self._state = target

    async def start(self) -> None:
        self._transition(KernelState.READY)
        await self._events.publish(KernelEvent(event_type=EventType.KERNEL_STARTED))

    async def stop(self) -> None:
        self._transition(KernelState.SHUTTING_DOWN)
        self._transition(KernelState.STOPPED)
        await self._events.publish(KernelEvent(event_type=EventType.KERNEL_STOPPED))

    async def process(self, request: RequestContext) -> dict[str, Any]:
        """Process request through full constitutional pipeline."""
        if self._state == KernelState.READY:
            self._transition(KernelState.PROCESSING)
        self._active_requests += 1
        exec_ctx = ExecutionContext()
        exec_ctx.start()
        await self._events.publish(
            KernelEvent(event_type=EventType.REQUEST_STARTED, request_id=request.request_id)
        )
        pipeline_output: dict[str, Any] = {}
        success = False
        try:
            for stage in PIPELINE_STAGES:
                if request.is_over_budget:
                    raise BudgetExceededError()
                if request.is_over_deadline:
                    raise KernelError("Deadline exceeded", category=FailureCategory.TIMEOUT)
                engine = self._registry.get(stage)
                if engine is None:
                    continue
                request.current_step = stage
                exec_ctx.current_engine = stage
                start_t = time.perf_counter()
                try:
                    result = await engine.process(pipeline_output)
                except Exception as exc:
                    dur = (time.perf_counter() - start_t) * 1000
                    exec_ctx.record_engine_time(stage, dur)
                    if exec_ctx.can_retry:
                        exec_ctx.retry_count += 1
                        continue
                    raise EngineError(f"Engine '{stage}' failed: {exc}", engine=stage) from exc
                dur = (time.perf_counter() - start_t) * 1000
                exec_ctx.record_engine_time(stage, dur)
                self._metrics.record_engine_time(stage, dur)
                if result.success:
                    pipeline_output[stage] = result.output
                    request.mark_engine_complete(stage, result.output)
                    request.add_tokens(result.tokens_used)
            exec_ctx.complete()
            success = True
            return {
                "success": True,
                "output": pipeline_output,
                "request_id": request.request_id,
                "elapsed_ms": exec_ctx.elapsed_ms,
                "tokens_used": request.tokens_used,
            }
        except KernelError as exc:
            exec_ctx.fail()
            return {
                "success": False,
                "error": str(exc),
                "category": exc.category.value,
                "request_id": request.request_id,
                "elapsed_ms": exec_ctx.elapsed_ms,
            }
        finally:
            self._active_requests -= 1
            if self._active_requests == 0 and self._state == KernelState.PROCESSING:
                self._transition(KernelState.READY)
            self._metrics.record_request(
                success, exec_ctx.elapsed_ms, request.tokens_used, request.cost
            )
            await self._events.publish(
                KernelEvent(
                    event_type=EventType.REQUEST_COMPLETED,
                    request_id=request.request_id,
                    data={"success": success},
                )
            )

    def get_status(self) -> dict[str, Any]:
        return {
            "state": self._state.value,
            "engines_registered": self._registry.engine_count,
            "active_requests": self._active_requests,
            "metrics": self._metrics.to_dict(),
            "world": self._world.to_dict(),
        }
