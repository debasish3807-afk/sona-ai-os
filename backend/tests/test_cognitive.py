"""Cognitive Kernel tests — 40+ tests covering all components."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))


# Helper: mock engine for testing
def make_mock_engine(engine_id: str, output: dict | None = None, fail: bool = False):
    from cognitive.engine_protocol import CognitiveEngine, EngineInfo, EngineResult, EngineState

    class MockEngine(CognitiveEngine):
        def __init__(self):
            self._info = EngineInfo(engine_id=engine_id, name=f"Mock {engine_id}", version="1.0.0")
            self._state = EngineState.READY

        @property
        def info(self):
            return self._info

        @property
        def state(self):
            return self._state

        async def initialize(self):
            pass

        async def start(self):
            self._state = EngineState.READY

        async def pause(self):
            self._state = EngineState.PAUSED

        async def resume(self):
            self._state = EngineState.READY

        async def stop(self):
            self._state = EngineState.STOPPED

        async def shutdown(self):
            self._state = EngineState.STOPPED

        async def health(self):
            return True

        def metrics(self):
            return {"calls": 0}

        async def process(self, context: dict[str, Any]) -> EngineResult:
            if fail:
                raise RuntimeError(f"{engine_id} failed")
            return EngineResult(
                engine_id=engine_id,
                success=True,
                output=output or {"result": engine_id},
                tokens_used=10,
            )

    return MockEngine()


class TestLifecycle:
    def test_valid_transitions(self):
        from cognitive.lifecycle import KernelState, can_transition

        assert can_transition(KernelState.STARTING, KernelState.READY) is True
        assert can_transition(KernelState.READY, KernelState.PROCESSING) is True
        assert can_transition(KernelState.PROCESSING, KernelState.READY) is True
        assert can_transition(KernelState.READY, KernelState.SHUTTING_DOWN) is True
        assert can_transition(KernelState.SHUTTING_DOWN, KernelState.STOPPED) is True

    def test_invalid_transitions(self):
        from cognitive.lifecycle import KernelState, can_transition

        assert can_transition(KernelState.STOPPED, KernelState.READY) is False
        assert can_transition(KernelState.STARTING, KernelState.PROCESSING) is False
        assert can_transition(KernelState.PAUSED, KernelState.PROCESSING) is False


class TestEngineRegistry:
    def test_register_and_get(self):
        from cognitive.engine_registry import EngineRegistry

        reg = EngineRegistry()
        engine = make_mock_engine("intent")
        reg.register(engine)
        assert reg.has_engine("intent")
        assert reg.get("intent") is engine
        assert reg.engine_count == 1

    def test_unregister(self):
        from cognitive.engine_registry import EngineRegistry

        reg = EngineRegistry()
        reg.register(make_mock_engine("goal"))
        assert reg.unregister("goal") is True
        assert reg.has_engine("goal") is False

    def test_replace(self):
        from cognitive.engine_registry import EngineRegistry

        reg = EngineRegistry()
        e1 = make_mock_engine("ctx")
        e2 = make_mock_engine("ctx")
        reg.register(e1)
        old = reg.replace(e2)
        assert old is e1
        assert reg.get("ctx") is e2

    def test_duplicate_register_raises(self):
        from cognitive.engine_registry import EngineRegistry
        from cognitive.exceptions import RegistryError

        reg = EngineRegistry()
        reg.register(make_mock_engine("dup"))
        raised = False
        try:
            reg.register(make_mock_engine("dup"))
        except RegistryError:
            raised = True
        assert raised

    def test_get_required_raises(self):
        from cognitive.engine_registry import EngineRegistry
        from cognitive.exceptions import RegistryError

        reg = EngineRegistry()
        raised = False
        try:
            reg.get_required("missing")
        except RegistryError:
            raised = True
        assert raised

    def test_list_engines(self):
        from cognitive.engine_registry import EngineRegistry

        reg = EngineRegistry()
        reg.register(make_mock_engine("a"))
        reg.register(make_mock_engine("b"))
        infos = reg.list_engines()
        assert len(infos) == 2

    def test_health_check_all(self):
        from cognitive.engine_registry import EngineRegistry

        reg = EngineRegistry()
        reg.register(make_mock_engine("h1"))
        reg.register(make_mock_engine("h2"))
        results = asyncio.run(reg.health_check_all())
        assert results == {"h1": True, "h2": True}


class TestEventBus:
    def test_publish_and_subscribe(self):
        from cognitive.event_bus import EventBus
        from cognitive.kernel_events import EventType, KernelEvent

        bus = EventBus()
        received = []

        async def handler(e: KernelEvent):
            received.append(e)

        bus.subscribe(EventType.REQUEST_STARTED, handler)
        asyncio.run(bus.publish(KernelEvent(event_type=EventType.REQUEST_STARTED)))
        assert len(received) == 1

    def test_subscribe_all(self):
        from cognitive.event_bus import EventBus
        from cognitive.kernel_events import EventType, KernelEvent

        bus = EventBus()
        received = []

        async def handler(e):
            received.append(e)

        bus.subscribe_all(handler)
        asyncio.run(bus.publish(KernelEvent(event_type=EventType.KERNEL_STARTED)))
        asyncio.run(bus.publish(KernelEvent(event_type=EventType.KERNEL_STOPPED)))
        assert len(received) == 2

    def test_middleware_filter(self):
        from cognitive.event_bus import EventBus
        from cognitive.kernel_events import EventType, KernelEvent

        bus = EventBus()
        received = []

        def block_all(e):
            return None  # Filter everything

        bus.add_middleware(block_all)

        async def handler(e):
            received.append(e)

        bus.subscribe(EventType.REQUEST_STARTED, handler)
        asyncio.run(bus.publish(KernelEvent(event_type=EventType.REQUEST_STARTED)))
        assert len(received) == 0

    def test_event_history(self):
        from cognitive.event_bus import EventBus
        from cognitive.kernel_events import EventType, KernelEvent

        bus = EventBus()
        asyncio.run(bus.publish(KernelEvent(event_type=EventType.KERNEL_STARTED, request_id="r1")))
        history = bus.get_history(request_id="r1")
        assert len(history) == 1
        assert history[0]["request_id"] == "r1"

    def test_event_count(self):
        from cognitive.event_bus import EventBus
        from cognitive.kernel_events import EventType, KernelEvent

        bus = EventBus()
        asyncio.run(bus.publish(KernelEvent(event_type=EventType.KERNEL_STARTED)))
        asyncio.run(bus.publish(KernelEvent(event_type=EventType.KERNEL_STOPPED)))
        assert bus.event_count == 2

    def test_unsubscribe(self):
        from cognitive.event_bus import EventBus
        from cognitive.kernel_events import EventType, KernelEvent

        bus = EventBus()
        received = []

        async def handler(e):
            received.append(e)

        bus.subscribe(EventType.KERNEL_STARTED, handler)
        bus.unsubscribe(EventType.KERNEL_STARTED, handler)
        asyncio.run(bus.publish(KernelEvent(event_type=EventType.KERNEL_STARTED)))
        assert len(received) == 0


class TestRequestContext:
    def test_creation(self):
        from cognitive.request_context import RequestContext

        ctx = RequestContext(session_id="s1", user_id="u1")
        assert ctx.session_id == "s1"
        assert ctx.request_id != ""
        assert ctx.remaining_budget == 100000

    def test_token_tracking(self):
        from cognitive.request_context import RequestContext

        ctx = RequestContext(token_budget=1000)
        ctx.add_tokens(500)
        assert ctx.tokens_used == 500
        assert ctx.remaining_budget == 500
        assert ctx.is_over_budget is False
        ctx.add_tokens(600)
        assert ctx.is_over_budget is True

    def test_engine_completion(self):
        from cognitive.request_context import RequestContext

        ctx = RequestContext()
        ctx.mark_engine_complete("intent", {"category": "code"})
        assert "intent" in ctx.completed_engines
        assert ctx.engine_results["intent"] == {"category": "code"}

    def test_serialization(self):
        from cognitive.request_context import RequestContext

        ctx = RequestContext(session_id="s", user_id="u")
        d = ctx.to_dict()
        assert d["session_id"] == "s"
        assert d["user_id"] == "u"
        assert "elapsed_seconds" in d


class TestExecutionContext:
    def test_lifecycle(self):
        from cognitive.execution_context import ExecutionContext, ExecutionState

        ctx = ExecutionContext()
        assert ctx.state == ExecutionState.PENDING
        ctx.start()
        assert ctx.state == ExecutionState.RUNNING
        ctx.complete()
        assert ctx.state == ExecutionState.COMPLETED
        assert ctx.elapsed_ms > 0

    def test_cancellation(self):
        from cognitive.execution_context import ExecutionContext

        ctx = ExecutionContext()
        assert ctx.is_cancelled is False
        ctx.cancel()
        assert ctx.is_cancelled is True

    def test_retry_tracking(self):
        from cognitive.execution_context import ExecutionContext

        ctx = ExecutionContext(max_retries=2)
        assert ctx.can_retry is True
        ctx.retry_count = 2
        assert ctx.can_retry is False

    def test_checkpoint(self):
        from cognitive.execution_context import ExecutionContext

        ctx = ExecutionContext()
        ctx.add_checkpoint("intent", {"data": "test"})
        assert len(ctx.checkpoints) == 1
        assert ctx.checkpoints[0].engine_id == "intent"

    def test_timeline(self):
        from cognitive.execution_context import ExecutionContext

        ctx = ExecutionContext()
        ctx.record_engine_time("intent", 50.0)
        ctx.record_engine_time("goal", 30.0)
        assert ctx.timeline["intent"] == 50.0
        assert "intent" in ctx.completed_engines


class TestWorldState:
    def test_creation(self):
        from cognitive.world_state import WorldState

        ws = WorldState(current_project="sona", environment="production")
        assert ws.current_project == "sona"
        assert ws.environment == "production"

    def test_serialization(self):
        from cognitive.world_state import WorldState

        ws = WorldState(system_health="degraded", running_tasks=3)
        d = ws.to_dict()
        assert d["system_health"] == "degraded"
        assert d["running_tasks"] == 3


class TestKernelMetrics:
    def test_record_request(self):
        from cognitive.metrics import KernelMetrics

        m = KernelMetrics()
        m.record_request(True, 100.0, 500, 0.01)
        m.record_request(False, 200.0, 300, 0.005)
        assert m.total_requests == 2
        assert m.completed_requests == 1
        assert m.failed_requests == 1
        assert m.success_rate == 0.5
        assert m.total_tokens == 800

    def test_engine_times(self):
        from cognitive.metrics import KernelMetrics

        m = KernelMetrics()
        m.record_engine_time("intent", 10.0)
        m.record_engine_time("intent", 20.0)
        d = m.to_dict()
        assert d["engine_avg_ms"]["intent"] == 15.0


class TestKernelEvents:
    def test_event_creation(self):
        from cognitive.kernel_events import EventType, KernelEvent

        e = KernelEvent(event_type=EventType.REQUEST_STARTED, request_id="r1")
        assert e.event_type == EventType.REQUEST_STARTED
        assert e.request_id == "r1"
        assert e.event_id != ""

    def test_event_serialization(self):
        from cognitive.kernel_events import EventType, KernelEvent

        e = KernelEvent(event_type=EventType.GOAL_CREATED, data={"goal": "test"})
        d = e.to_dict()
        assert d["event_type"] == "goal.created"
        assert d["data"]["goal"] == "test"


class TestCognitiveKernel:
    def test_kernel_start_stop(self):
        from cognitive.kernel import CognitiveKernel
        from cognitive.lifecycle import KernelState

        k = CognitiveKernel()
        asyncio.run(k.start())
        assert k.state == KernelState.READY
        asyncio.run(k.stop())
        assert k.state == KernelState.STOPPED

    def test_process_empty_pipeline(self):
        from cognitive.kernel import CognitiveKernel
        from cognitive.request_context import RequestContext

        k = CognitiveKernel()
        asyncio.run(k.start())
        req = RequestContext(session_id="s1")
        result = asyncio.run(k.process(req))
        assert result["success"] is True

    def test_process_with_engines(self):
        from cognitive.kernel import CognitiveKernel
        from cognitive.request_context import RequestContext

        k = CognitiveKernel()
        k.registry.register(make_mock_engine("intent"))
        k.registry.register(make_mock_engine("goal"))
        asyncio.run(k.start())
        req = RequestContext()
        result = asyncio.run(k.process(req))
        assert result["success"] is True
        assert "intent" in result["output"]
        assert "goal" in result["output"]

    def test_process_engine_failure(self):
        from cognitive.kernel import CognitiveKernel
        from cognitive.request_context import RequestContext

        k = CognitiveKernel()
        k.registry.register(make_mock_engine("intent", fail=True))
        asyncio.run(k.start())
        req = RequestContext()
        asyncio.run(k.process(req))
        assert k.metrics.total_requests == 1

    def test_budget_exceeded(self):
        from cognitive.kernel import CognitiveKernel
        from cognitive.request_context import RequestContext

        k = CognitiveKernel()
        k.registry.register(make_mock_engine("intent"))
        asyncio.run(k.start())
        req = RequestContext(token_budget=0)
        asyncio.run(k.process(req))
        assert k.metrics.total_requests == 1

    def test_get_status(self):
        from cognitive.kernel import CognitiveKernel

        k = CognitiveKernel()
        asyncio.run(k.start())
        status = k.get_status()
        assert status["state"] == "ready"
        assert "metrics" in status
        assert "world" in status


class TestExceptions:
    def test_kernel_error(self):
        from cognitive.exceptions import FailureCategory, KernelError

        err = KernelError("test", category=FailureCategory.TRANSIENT, retryable=True)
        assert str(err) == "test"
        assert err.category == FailureCategory.TRANSIENT
        assert err.retryable is True

    def test_budget_exceeded(self):
        from cognitive.exceptions import BudgetExceededError, FailureCategory

        err = BudgetExceededError()
        assert err.category == FailureCategory.RESOURCE

    def test_cancellation_error(self):
        from cognitive.exceptions import CancellationError, FailureCategory

        err = CancellationError()
        assert err.category == FailureCategory.CANCELLED
