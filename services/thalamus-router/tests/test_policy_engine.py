"""Unit tests for the PolicyEngine."""

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.domain.policies import PolicyAction, RoutingPolicy
from sona_thalamus.infrastructure.policy_engine import PolicyEngine


class TestPolicyEngine:
    """Tests for routing policy evaluation."""

    def setup_method(self) -> None:
        """Create a fresh policy engine for each test."""
        self.engine = PolicyEngine()

    def test_default_policies_allow_all(self) -> None:
        """Test that default policies allow all intents."""
        action = self.engine.get_effective_action(IntentCategory.CHAT, "Hello")
        assert action == PolicyAction.ALLOW

    def test_default_allow_code(self) -> None:
        """Test default policy allows code intent."""
        action = self.engine.get_effective_action(IntentCategory.CODE, "Write code")
        assert action == PolicyAction.ALLOW

    def test_custom_deny_policy(self) -> None:
        """Test custom deny policy blocks routing."""
        policies = [
            RoutingPolicy(
                name="deny_automation",
                condition="intent == automation",
                action=PolicyAction.DENY,
                priority=0,
            ),
        ]
        engine = PolicyEngine(policies=policies)
        action = engine.get_effective_action(IntentCategory.AUTOMATION, "Automate this")
        assert action == PolicyAction.DENY

    def test_policy_priority_ordering(self) -> None:
        """Test that lower priority number takes precedence."""
        policies = [
            RoutingPolicy(
                name="deny_all",
                condition="always",
                action=PolicyAction.DENY,
                priority=10,
            ),
            RoutingPolicy(
                name="allow_code",
                condition="intent == code",
                action=PolicyAction.ALLOW,
                priority=1,
            ),
        ]
        engine = PolicyEngine(policies=policies)
        action = engine.get_effective_action(IntentCategory.CODE, "Write code")
        assert action == PolicyAction.ALLOW

    def test_content_contains_condition(self) -> None:
        """Test content-based policy condition."""
        policies = [
            RoutingPolicy(
                name="block_dangerous",
                condition="content contains dangerous",
                action=PolicyAction.DENY,
                priority=0,
            ),
        ]
        engine = PolicyEngine(policies=policies)
        action = engine.get_effective_action(IntentCategory.CHAT, "This is dangerous stuff")
        assert action == PolicyAction.DENY

    def test_content_not_matching(self) -> None:
        """Test policy doesn't match when content doesn't contain keyword."""
        policies = [
            RoutingPolicy(
                name="block_dangerous",
                condition="content contains dangerous",
                action=PolicyAction.DENY,
                priority=0,
            ),
        ]
        engine = PolicyEngine(policies=policies)
        action = engine.get_effective_action(IntentCategory.CHAT, "Hello world")
        assert action == PolicyAction.ALLOW

    def test_evaluate_returns_evaluations(self) -> None:
        """Test evaluate returns list of policy evaluations."""
        evaluations = self.engine.evaluate(IntentCategory.CHAT, "Hello")
        assert len(evaluations) > 0
        assert evaluations[0].matched is True

    def test_add_policy(self) -> None:
        """Test adding a policy at runtime."""
        policy = RoutingPolicy(
            name="rate_limit_research",
            condition="intent == research",
            action=PolicyAction.RATE_LIMIT,
            priority=0,
        )
        self.engine.add_policy(policy)
        action = self.engine.get_effective_action(IntentCategory.RESEARCH, "Search")
        assert action == PolicyAction.RATE_LIMIT

    def test_intent_not_equal_condition(self) -> None:
        """Test intent != condition."""
        policies = [
            RoutingPolicy(
                name="allow_non_system",
                condition="intent != system",
                action=PolicyAction.ALLOW,
                priority=0,
            ),
        ]
        engine = PolicyEngine(policies=policies)
        action = engine.get_effective_action(IntentCategory.CHAT, "Hello")
        assert action == PolicyAction.ALLOW

    def test_no_matching_policies(self) -> None:
        """Test that no matching policies defaults to ALLOW."""
        policies = [
            RoutingPolicy(
                name="only_code",
                condition="intent == code",
                action=PolicyAction.DENY,
                priority=0,
            ),
        ]
        engine = PolicyEngine(policies=policies)
        action = engine.get_effective_action(IntentCategory.CHAT, "Hello")
        assert action == PolicyAction.ALLOW

    def test_redirect_policy(self) -> None:
        """Test redirect policy action."""
        policies = [
            RoutingPolicy(
                name="redirect_chat",
                condition="intent == chat",
                action=PolicyAction.REDIRECT,
                target="special-service",
                priority=0,
            ),
        ]
        engine = PolicyEngine(policies=policies)
        action = engine.get_effective_action(IntentCategory.CHAT, "Hello")
        assert action == PolicyAction.REDIRECT
