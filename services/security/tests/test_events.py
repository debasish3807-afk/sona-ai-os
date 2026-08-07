"""Tests for domain events."""

from dataclasses import FrozenInstanceError

import pytest

from sona_security.domain.events import (
    AuthenticationFailedEvent,
    AuthenticationSucceededEvent,
    PermissionDeniedEvent,
    SecurityThreatEvent,
    TokenRevokedEvent,
)


class TestAuthenticationSucceededEvent:
    def test_creation_defaults(self) -> None:
        event = AuthenticationSucceededEvent()
        assert event.user_id == ""
        assert event.method == ""

    def test_creation_with_values(self) -> None:
        event = AuthenticationSucceededEvent(user_id="user-1", method="password")
        assert event.user_id == "user-1"
        assert event.method == "password"

    def test_is_frozen(self) -> None:
        event = AuthenticationSucceededEvent(user_id="u")
        with pytest.raises((FrozenInstanceError, AttributeError)):
            event.user_id = "changed"  # type: ignore[misc]

    def test_has_event_id(self) -> None:
        event = AuthenticationSucceededEvent()
        assert event.event_id is not None

    def test_has_occurred_at(self) -> None:
        event = AuthenticationSucceededEvent()
        assert event.occurred_at is not None


class TestAuthenticationFailedEvent:
    def test_creation_defaults(self) -> None:
        event = AuthenticationFailedEvent()
        assert event.username == ""
        assert event.reason == ""
        assert event.ip_address == ""

    def test_creation_with_values(self) -> None:
        event = AuthenticationFailedEvent(
            username="alice", reason="bad_password", ip_address="192.168.1.1"
        )
        assert event.username == "alice"
        assert event.reason == "bad_password"
        assert event.ip_address == "192.168.1.1"

    def test_is_frozen(self) -> None:
        event = AuthenticationFailedEvent(username="bob")
        with pytest.raises((FrozenInstanceError, AttributeError)):
            event.username = "changed"  # type: ignore[misc]


class TestTokenRevokedEvent:
    def test_creation_defaults(self) -> None:
        event = TokenRevokedEvent()
        assert event.user_id == ""
        assert event.token_id == ""

    def test_creation_with_values(self) -> None:
        event = TokenRevokedEvent(user_id="user-1", token_id="tok-abc")
        assert event.user_id == "user-1"
        assert event.token_id == "tok-abc"

    def test_is_frozen(self) -> None:
        event = TokenRevokedEvent(user_id="u")
        with pytest.raises((FrozenInstanceError, AttributeError)):
            event.user_id = "x"  # type: ignore[misc]


class TestPermissionDeniedEvent:
    def test_creation_defaults(self) -> None:
        event = PermissionDeniedEvent()
        assert event.user_id == ""
        assert event.resource == ""
        assert event.action == ""

    def test_creation_with_values(self) -> None:
        event = PermissionDeniedEvent(user_id="user-2", resource="agents", action="delete")
        assert event.user_id == "user-2"
        assert event.resource == "agents"
        assert event.action == "delete"

    def test_is_frozen(self) -> None:
        event = PermissionDeniedEvent(user_id="u")
        with pytest.raises((FrozenInstanceError, AttributeError)):
            event.resource = "x"  # type: ignore[misc]


class TestSecurityThreatEvent:
    def test_creation_defaults(self) -> None:
        event = SecurityThreatEvent()
        assert event.threat_type == ""
        assert event.content_hash == ""
        assert event.user_id == ""
        assert event.blocked is True

    def test_creation_with_values(self) -> None:
        event = SecurityThreatEvent(
            threat_type="prompt_injection",
            content_hash="abc123",
            user_id="user-3",
            blocked=False,
        )
        assert event.threat_type == "prompt_injection"
        assert event.content_hash == "abc123"
        assert event.user_id == "user-3"
        assert event.blocked is False

    def test_is_frozen(self) -> None:
        event = SecurityThreatEvent(threat_type="test")
        with pytest.raises((FrozenInstanceError, AttributeError)):
            event.blocked = False  # type: ignore[misc]
