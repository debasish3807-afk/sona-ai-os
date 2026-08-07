"""Unit tests for MCP domain events."""

from sona_mcp.domain.events import (
    ServerConnectedEvent,
    ServerDisconnectedEvent,
    ToolFailedEvent,
    ToolInvokedEvent,
    ToolRegisteredEvent,
)


class TestToolRegisteredEvent:
    def test_creation_defaults(self) -> None:
        event = ToolRegisteredEvent()
        assert event.tool_name == ""
        assert event.server_id == ""

    def test_creation_with_values(self) -> None:
        event = ToolRegisteredEvent(tool_name="read_file", server_id="srv-1")
        assert event.tool_name == "read_file"
        assert event.server_id == "srv-1"

    def test_has_event_id(self) -> None:
        event = ToolRegisteredEvent()
        assert event.event_id is not None

    def test_has_occurred_at(self) -> None:
        event = ToolRegisteredEvent()
        assert event.occurred_at is not None

    def test_is_frozen(self) -> None:
        event = ToolRegisteredEvent(tool_name="test")
        try:
            event.tool_name = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except (TypeError, AttributeError):
            pass


class TestToolInvokedEvent:
    def test_creation_defaults(self) -> None:
        event = ToolInvokedEvent()
        assert event.tool_name == ""
        assert event.user_id == ""
        assert event.success is True
        assert event.duration_ms == 0.0

    def test_creation_with_values(self) -> None:
        event = ToolInvokedEvent(tool_name="calc", user_id="u1", success=False, duration_ms=42.5)
        assert event.tool_name == "calc"
        assert event.user_id == "u1"
        assert event.success is False
        assert event.duration_ms == 42.5

    def test_successful_invocation(self) -> None:
        event = ToolInvokedEvent(tool_name="echo", user_id="u1", success=True)
        assert event.success is True

    def test_failed_invocation(self) -> None:
        event = ToolInvokedEvent(tool_name="web_fetch", user_id="u2", success=False)
        assert event.success is False


class TestToolFailedEvent:
    def test_creation_defaults(self) -> None:
        event = ToolFailedEvent()
        assert event.tool_name == ""
        assert event.error == ""

    def test_creation_with_values(self) -> None:
        event = ToolFailedEvent(tool_name="read_file", error="Permission denied")
        assert event.tool_name == "read_file"
        assert event.error == "Permission denied"

    def test_unique_event_ids(self) -> None:
        e1 = ToolFailedEvent()
        e2 = ToolFailedEvent()
        assert e1.event_id != e2.event_id


class TestServerConnectedEvent:
    def test_creation_defaults(self) -> None:
        event = ServerConnectedEvent()
        assert event.server_id == ""
        assert event.tools_count == 0

    def test_creation_with_values(self) -> None:
        event = ServerConnectedEvent(server_id="srv-1", tools_count=5)
        assert event.server_id == "srv-1"
        assert event.tools_count == 5


class TestServerDisconnectedEvent:
    def test_creation_defaults(self) -> None:
        event = ServerDisconnectedEvent()
        assert event.server_id == ""
        assert event.reason == ""

    def test_creation_with_values(self) -> None:
        event = ServerDisconnectedEvent(server_id="srv-2", reason="timeout")
        assert event.server_id == "srv-2"
        assert event.reason == "timeout"
