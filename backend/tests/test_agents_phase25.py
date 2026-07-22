"""Comprehensive tests for Phase 25: Multi-Agent Framework."""

import pytest

from agents.concrete_agents import (
    AutomationAgent,
    CodingAgent,
    MemoryAgent,
    PlannerAgent,
    ResearchAgent,
    ReviewAgent,
    create_agent,
)
from agents.context import ExecutionContext
from agents.messaging import AgentMessage, MessageBus, MessageType
from agents.orchestrator import AgentOrchestrator
from agents.task_queue import TaskQueue, TaskStatus


class TestConcreteAgents:
    """Test all 6 concrete agent implementations."""

    @pytest.fixture
    def ctx(self):
        return ExecutionContext(
            session_id="test",
            task_id="t1",
            agent_id="a1",
            input_data={"task": "test task", "code": "x = 1", "language": "python"},
        )

    @pytest.mark.asyncio
    async def test_planner_agent(self, ctx):
        agent = PlannerAgent()
        await agent.initialize()
        assert agent.status.value == "idle"
        result = await agent.execute(ctx)
        assert result.success
        assert "steps" in result.output
        assert result.output["agent_type"] == "planner"

    @pytest.mark.asyncio
    async def test_coding_agent(self, ctx):
        agent = CodingAgent()
        await agent.initialize()
        result = await agent.execute(ctx)
        assert result.success
        assert result.output["agent_type"] == "coding"

    @pytest.mark.asyncio
    async def test_review_agent(self, ctx):
        agent = ReviewAgent()
        await agent.initialize()
        result = await agent.execute(ctx)
        assert result.success
        assert "issues" in result.output

    @pytest.mark.asyncio
    async def test_research_agent(self, ctx):
        agent = ResearchAgent()
        await agent.initialize()
        ctx.input_data = {"query": "test research topic"}
        result = await agent.execute(ctx)
        assert result.success
        assert result.output["agent_type"] == "research"

    @pytest.mark.asyncio
    async def test_memory_agent(self, ctx):
        agent = MemoryAgent()
        await agent.initialize()
        ctx.input_data = {"operation": "store", "content": "test memory"}
        result = await agent.execute(ctx)
        assert result.success
        assert result.output["agent_type"] == "memory"

    @pytest.mark.asyncio
    async def test_automation_agent(self, ctx):
        agent = AutomationAgent()
        await agent.initialize()
        ctx.input_data = {"trigger": "test", "action": "run"}
        result = await agent.execute(ctx)
        assert result.success
        assert result.output["agent_type"] == "automation"

    @pytest.mark.asyncio
    async def test_agent_properties(self):
        for _cls_name, cls in [("PlannerAgent", PlannerAgent), ("CodingAgent", CodingAgent)]:
            agent = cls()
            assert agent.info.agent_id is not None
            assert agent.info.name is not None
            assert len(agent.capabilities.capabilities) > 0

    def test_create_agent_factory(self):
        agent = create_agent("planner")
        assert isinstance(agent, PlannerAgent)
        agent = create_agent("coding")
        assert isinstance(agent, CodingAgent)
        with pytest.raises(ValueError):
            create_agent("nonexistent")


class TestTaskQueue:
    """Test task queue with priority and retry."""

    def test_enqueue_dequeue(self):
        q = TaskQueue()
        tid = q.enqueue("planner", "test task", {"key": "val"}, priority=10)
        assert tid is not None
        task = q.dequeue("planner")
        assert task is not None
        assert task.task_id == tid
        assert task.status == TaskStatus.ASSIGNED

    def test_priority_ordering(self):
        q = TaskQueue()
        q.enqueue("planner", "low", priority=100)
        high = q.enqueue("planner", "high", priority=1)
        task = q.dequeue("planner")
        assert task.task_id == high  # higher priority dequeued first

    def test_retry_logic(self):
        q = TaskQueue()
        tid = q.enqueue("general", "retry me", max_retries=2)
        q.fail(tid, "error 1")
        assert q.get(tid).retry_count == 1
        assert q.get(tid).status == TaskStatus.QUEUED  # retried
        q.fail(tid, "error 2")
        assert q.get(tid).retry_count == 2
        assert q.get(tid).status == TaskStatus.QUEUED
        q.fail(tid, "error 3")
        assert q.get(tid).status == TaskStatus.FAILED  # max retries exceeded

    def test_complete_task(self):
        q = TaskQueue()
        tid = q.enqueue("coding", "write code")
        q.complete(tid, {"output": "done"})
        assert q.get(tid).status == TaskStatus.COMPLETED
        assert q.get(tid).result["output"] == "done"

    def test_cancel_task(self):
        q = TaskQueue()
        tid = q.enqueue("research", "cancel me")
        assert q.cancel(tid)
        assert q.get(tid).status == TaskStatus.CANCELLED

    def test_list_tasks(self):
        q = TaskQueue()
        q.enqueue("a", "task a", priority=1)
        q.enqueue("b", "task b", priority=2)
        tasks = q.list_tasks()
        assert len(tasks) >= 2

    def test_get_stats(self):
        q = TaskQueue()
        q.enqueue("x", "test")
        stats = q.get_stats()
        assert stats["total"] == 1
        assert stats.get("queued") == 1

    def test_queue_full(self):
        q = TaskQueue()
        q._max_size = 2
        q.enqueue("a", "1")
        q.enqueue("b", "2")
        with pytest.raises(RuntimeError):
            q.enqueue("c", "3")


class TestMessageBus:
    """Test inter-agent messaging."""

    @pytest.mark.asyncio
    async def test_send_receive(self):
        bus = MessageBus()
        msg = AgentMessage(sender_id="a1", recipient_id="a2", payload={"text": "hello"})
        msg_id = await bus.send(msg)
        assert msg_id is not None
        inbox = await bus.receive("a2")
        assert len(inbox) == 1
        assert inbox[0].payload["text"] == "hello"

    @pytest.mark.asyncio
    async def test_request_response(self):
        bus = MessageBus()
        req = AgentMessage(
            msg_type=MessageType.REQUEST,
            sender_id="a1",
            recipient_id="a2",
            payload={"q": "what"},
            correlation_id="corr-1",
        )
        await bus.send(req)
        resp = AgentMessage(
            msg_type=MessageType.RESPONSE,
            sender_id="a2",
            recipient_id="a1",
            payload={"answer": "42"},
            correlation_id="corr-1",
        )
        await bus.send(resp)
        inbox = await bus.receive("a1")
        assert len(inbox) >= 1
        matching = [m for m in inbox if m.correlation_id == "corr-1"]
        assert len(matching) >= 1

    @pytest.mark.asyncio
    async def test_broadcast(self):
        bus = MessageBus()
        msg = AgentMessage(sender_id="a1", payload={"alert": "test"})
        ids = await bus.broadcast(msg, ["a2", "a3", "a4"])
        assert len(ids) == 3
        assert len(await bus.receive("a2")) == 1
        assert len(await bus.receive("a3")) == 1

    @pytest.mark.asyncio
    async def test_subscribe_publish(self):
        bus = MessageBus()
        await bus.subscribe("a1", "topic1")
        await bus.subscribe("a2", "topic1")
        subscribers = await bus.publish("topic1", {"data": "test"})
        assert len(subscribers) == 2

    def test_message_expiry(self):
        import time

        msg = AgentMessage(sender_id="a", recipient_id="b", ttl_seconds=0.001)
        assert not msg.is_expired()  # just created
        time.sleep(0.01)
        assert msg.is_expired()


class TestAgentOrchestrator:
    """Test the full agent orchestration system."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        orch = AgentOrchestrator()
        await orch.initialize()
        agents = await orch.get_agents()
        assert len(agents) >= 6  # 6 default agent types
        assert orch._initialized

    @pytest.mark.asyncio
    async def test_submit_and_execute(self):
        orch = AgentOrchestrator()
        await orch.initialize()
        tid = await orch.submit_task("planner", "plan a project", {"goal": "test"})
        assert tid is not None
        result = await orch.execute_next()
        assert result is not None
        assert result["task_id"] == tid

    @pytest.mark.asyncio
    async def test_stats(self):
        orch = AgentOrchestrator()
        await orch.initialize()
        stats = await orch.get_stats()
        assert stats["agents"] >= 6

    @pytest.mark.asyncio
    async def test_send_message(self):
        orch = AgentOrchestrator()
        await orch.initialize()
        agents = await orch.get_agents()
        if len(agents) >= 2:
            msg_id = await orch.send_message(
                agents[0]["agent_id"], agents[1]["agent_id"], {"test": "hello"}
            )
            assert msg_id is not None
