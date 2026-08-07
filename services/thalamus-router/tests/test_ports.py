"""Unit tests for Thalamus Router abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest
from sona_thalamus.application.ports import LoadBalancerPort, ThalamusRouterPort
from sona_thalamus.domain.models import IntentCategory, RequestPriority, RoutingDecision


class TestThalamusRouterPort:
    """Tests for the ThalamusRouterPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify ThalamusRouterPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ThalamusRouterPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = ThalamusRouterPort.__abstractmethods__
        assert "classify_intent" in abstract_methods
        assert "route" in abstract_methods
        assert "health_check" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteRouter(ThalamusRouterPort):
            async def classify_intent(self, content: str, context: dict) -> IntentCategory:
                return IntentCategory.CHAT

            async def route(self, request: dict) -> RoutingDecision:
                return RoutingDecision(
                    target_service="brain-os",
                    intent=IntentCategory.CHAT,
                    priority=RequestPriority.NORMAL,
                    requires_agents=[],
                    estimated_latency_ms=100,
                )

            async def health_check(self) -> dict[str, bool]:
                return {"brain-os": True, "memory-os": True}

        router = ConcreteRouter()
        assert isinstance(router, ThalamusRouterPort)

    @pytest.mark.asyncio
    async def test_classify_intent_returns_category(self) -> None:
        """Test that a concrete classify_intent returns an IntentCategory."""

        class MockRouter(ThalamusRouterPort):
            async def classify_intent(self, content: str, context: dict) -> IntentCategory:
                if "code" in content.lower():
                    return IntentCategory.CODE
                return IntentCategory.CHAT

            async def route(self, request: dict) -> RoutingDecision:
                return RoutingDecision(
                    target_service="brain-os",
                    intent=IntentCategory.CHAT,
                    priority=RequestPriority.NORMAL,
                    requires_agents=[],
                    estimated_latency_ms=100,
                )

            async def health_check(self) -> dict[str, bool]:
                return {}

        router = MockRouter()
        result = await router.classify_intent("Write me some code", {})
        assert result == IntentCategory.CODE

        result = await router.classify_intent("Hello, how are you?", {})
        assert result == IntentCategory.CHAT

    @pytest.mark.asyncio
    async def test_route_returns_routing_decision(self) -> None:
        """Test that a concrete route() returns a RoutingDecision."""

        class MockRouter(ThalamusRouterPort):
            async def classify_intent(self, content: str, context: dict) -> IntentCategory:
                return IntentCategory.RESEARCH

            async def route(self, request: dict) -> RoutingDecision:
                return RoutingDecision(
                    target_service="research-os",
                    intent=IntentCategory.RESEARCH,
                    priority=RequestPriority.HIGH,
                    requires_agents=["research"],
                    estimated_latency_ms=300,
                    fallback_service="brain-os",
                )

            async def health_check(self) -> dict[str, bool]:
                return {}

        router = MockRouter()
        decision = await router.route({"content": "Research AI trends"})
        assert isinstance(decision, RoutingDecision)
        assert decision.target_service == "research-os"
        assert decision.fallback_service == "brain-os"

    @pytest.mark.asyncio
    async def test_health_check_returns_dict(self) -> None:
        """Test that health_check returns service health map."""

        class MockRouter(ThalamusRouterPort):
            async def classify_intent(self, content: str, context: dict) -> IntentCategory:
                return IntentCategory.CHAT

            async def route(self, request: dict) -> RoutingDecision:
                return RoutingDecision(
                    target_service="brain-os",
                    intent=IntentCategory.CHAT,
                    priority=RequestPriority.NORMAL,
                    requires_agents=[],
                    estimated_latency_ms=100,
                )

            async def health_check(self) -> dict[str, bool]:
                return {
                    "brain-os": True,
                    "memory-os": True,
                    "knowledge-os": False,
                }

        router = MockRouter()
        health = await router.health_check()
        assert health["brain-os"] is True
        assert health["knowledge-os"] is False


class TestLoadBalancerPort:
    """Tests for the LoadBalancerPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify LoadBalancerPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LoadBalancerPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = LoadBalancerPort.__abstractmethods__
        assert "get_service_load" in abstract_methods
        assert "select_instance" in abstract_methods

    @pytest.mark.asyncio
    async def test_concrete_get_service_load(self) -> None:
        """Test that a concrete get_service_load returns a float."""

        class MockBalancer(LoadBalancerPort):
            async def get_service_load(self, service_name: str) -> float:
                loads = {"brain-os": 0.3, "memory-os": 0.7}
                return loads.get(service_name, 0.0)

            async def select_instance(self, service_name: str) -> str:
                return f"http://{service_name}-instance-1:8000"

        balancer = MockBalancer()
        load = await balancer.get_service_load("brain-os")
        assert load == 0.3
        assert 0.0 <= load <= 1.0

    @pytest.mark.asyncio
    async def test_concrete_select_instance(self) -> None:
        """Test that select_instance returns an instance identifier."""

        class MockBalancer(LoadBalancerPort):
            async def get_service_load(self, service_name: str) -> float:
                return 0.5

            async def select_instance(self, service_name: str) -> str:
                return f"http://{service_name}-pod-abc123:8000"

        balancer = MockBalancer()
        instance = await balancer.select_instance("ai-kernel")
        assert "ai-kernel" in instance
        assert isinstance(instance, str)
