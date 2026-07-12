"""Cognitive Kernel — the central orchestration runtime for Sona AI OS.

Implements the constitutional lifecycle: every request flows through
Intent → Goal → Context → Thinking → Reasoning → Planning → Decision
→ Execution → Verification → Learning → Memory → Response.
"""

from cognitive.engine_protocol import CognitiveEngine, EngineInfo, EngineResult, EngineState
from cognitive.engine_registry import EngineRegistry
from cognitive.event_bus import EventBus
from cognitive.execution_context import ExecutionContext, ExecutionState
from cognitive.kernel_events import EventType, KernelEvent
from cognitive.lifecycle import KernelState, can_transition
from cognitive.metrics import KernelMetrics
from cognitive.request_context import RequestContext
from cognitive.world_state import WorldState

__all__ = [
    "CognitiveEngine",
    "EngineInfo",
    "EngineRegistry",
    "EngineResult",
    "EngineState",
    "EventBus",
    "EventType",
    "ExecutionContext",
    "ExecutionState",
    "KernelEvent",
    "KernelMetrics",
    "KernelState",
    "RequestContext",
    "WorldState",
    "can_transition",
]
