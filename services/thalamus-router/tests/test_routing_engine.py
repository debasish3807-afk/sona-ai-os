"""Unit tests for the RoutingEngine."""

import pytest
from sona_thalamus.application.ports import ThalamusRouterPort
from sona_thalamus.domain.events import (
    ExecutionPlanCreatedEvent,
    IntentClassifiedEvent,
)
from sona_thalamus.domain.execution_plan import ExecutionPlan
from sona_thalamus.domain.models import IntentCategory, RequestPriority
from sona_thalamus.infrastructure.di import create_thalamus_router


class TestRoutingEngine:
    """Tests for the main routing engine."""

    def setup_method(self) -> None:
        """Create a fully wired routing engine."""
        self.engine = create_thalamus_router()

    def test_implements_port(self) -> None:
        """Test that RoutingEngine implements ThalamusRouterPort."""
        assert isinstance(self.engine, ThalamusRouterPort)

    @pytest.mark.asyncio
    async def test_classify_intent_code(self) -> None:
        """Test intent classification for code."""
        intent = await self.engine.classify_intent("Write code for a function", {})
        assert intent == IntentCategory.CODE

    @pytest.mark.asyncio
    async def test_classify_intent_chat(self) -> None:
        """Test intent classification falls back to chat."""
        intent = await self.engine.classify_intent("Hello, how are you?", {})
        assert intent == IntentCategory.CHAT

    @pytest.mark.asyncio
    async def test_classify_intent_research(self) -> None:
        """Test intent classification for research."""
        intent = await self.engine.classify_intent("What is quantum computing?", {})
        assert intent == IntentCategory.RESEARCH

    @pytest.mark.asyncio
    async def test_route_code_request(self) -> None:
        """Test routing a code request."""
        decision = await self.engine.route({"content": "Implement a function for sorting"})
        assert decision.intent == IntentCategory.CODE
        assert decision.target_service == "ai-engineering-os"
        assert decision.priority == RequestPriority.HIGH

    @pytest.mark.asyncio
    async def test_route_chat_request(self) -> None:
        """Test routing a chat request."""
        decision = await self.engine.route({"content": "Hello there!"})
        assert decision.intent == IntentCategory.CHAT
        assert decision.target_service == "brain-os"

    @pytest.mark.asyncio
    async def test_route_returns_agents(self) -> None:
        """Test that routing includes required agents."""
        decision = await self.engine.route({"content": "Write code for a complex algorithm"})
        assert isinstance(decision.requires_agents, list)

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test health check returns service status."""
        health = await self.engine.health_check()
        assert isinstance(health, dict)
        assert "brain-os" in health
        assert all(isinstance(v, bool) for v in health.values())

    @pytest.mark.asyncio
    async def test_create_execution_plan_code(self) -> None:
        """Test execution plan creation for code request."""
        plan = await self.engine.create_execution_plan(
            {
                "content": "Implement a function class to refactor the algorithm",
                "session_id": "test-session",
            }
        )
        assert isinstance(plan, ExecutionPlan)
        assert plan.intent == "code"
        assert len(plan.steps) > 0
        assert plan.model_id != ""

    @pytest.mark.asyncio
    async def test_create_execution_plan_chat_fallback(self) -> None:
        """Test execution plan for unclassified content uses fallback."""
        plan = await self.engine.create_execution_plan(
            {"content": "Hi", "session_id": "test-session"}
        )
        assert isinstance(plan, ExecutionPlan)
        assert plan.intent == "chat"

    @pytest.mark.asyncio
    async def test_events_emitted(self) -> None:
        """Test that domain events are emitted during routing."""
        await self.engine.classify_intent("Write code", {})
        events = self.engine.get_events()
        assert len(events) > 0
        assert any(isinstance(e, IntentClassifiedEvent) for e in events)

    @pytest.mark.asyncio
    async def test_execution_plan_events(self) -> None:
        """Test that plan creation emits events."""
        await self.engine.create_execution_plan(
            {"content": "Implement a function class to debug", "session_id": "s1"}
        )
        events = self.engine.get_events()
        assert any(isinstance(e, ExecutionPlanCreatedEvent) for e in events)

    @pytest.mark.asyncio
    async def test_route_empty_content(self) -> None:
        """Test routing with empty content."""
        decision = await self.engine.route({"content": ""})
        assert decision.intent == IntentCategory.CHAT

    @pytest.mark.asyncio
    async def test_routing_estimated_latency(self) -> None:
        """Test that routing includes latency estimate."""
        decision = await self.engine.route({"content": "Search for something"})
        assert decision.estimated_latency_ms > 0
