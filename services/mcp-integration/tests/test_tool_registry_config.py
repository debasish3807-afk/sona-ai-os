"""Tests for MCP tool registry configuration.

Verifies that demo tools are isolated from production tools and
controlled by environment configuration.
"""

import os
from unittest.mock import patch

from sona_mcp.infrastructure.tool_registry_config import (
    DEMO_TOOL_NAMES,
    PRODUCTION_TOOL_NAMES,
    get_demo_tools,
    get_production_tools,
    get_registered_handlers,
    get_registered_server,
    get_registered_tools,
    is_demo_tools_enabled,
)


class TestDemoToolsDisabledByDefault:
    """Demo tools must be disabled in production (default) mode."""

    def test_demo_tools_disabled_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert is_demo_tools_enabled() is False

    def test_demo_tools_disabled_when_false(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": "false"}):
            assert is_demo_tools_enabled() is False

    def test_demo_tools_disabled_when_empty(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": ""}):
            assert is_demo_tools_enabled() is False

    def test_registered_tools_excludes_demo_in_production(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": "false"}):
            tools = get_registered_tools()
            tool_names = {t.name for t in tools}
            assert tool_names == PRODUCTION_TOOL_NAMES
            assert not tool_names.intersection(DEMO_TOOL_NAMES)

    def test_registered_handlers_excludes_demo_in_production(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": "false"}):
            handlers = get_registered_handlers()
            assert "read_file" not in handlers
            assert "web_fetch" not in handlers
            assert "calculate" in handlers
            assert "current_time" in handlers
            assert "echo" in handlers

    def test_production_server_has_no_demo_tools(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": "false"}):
            server = get_registered_server()
            tool_names = {t.name for t in server.tools}
            assert not tool_names.intersection(DEMO_TOOL_NAMES)


class TestDemoToolsEnabledExplicitly:
    """Demo tools available only when explicitly enabled."""

    def test_demo_tools_enabled_with_true(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": "true"}):
            assert is_demo_tools_enabled() is True

    def test_demo_tools_enabled_with_1(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": "1"}):
            assert is_demo_tools_enabled() is True

    def test_registered_tools_includes_demo_when_enabled(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": "true"}):
            tools = get_registered_tools()
            tool_names = {t.name for t in tools}
            assert "read_file" in tool_names
            assert "web_fetch" in tool_names
            assert "calculate" in tool_names

    def test_registered_handlers_includes_demo_when_enabled(self) -> None:
        with patch.dict(os.environ, {"SONA_MCP_DEMO_TOOLS_ENABLED": "true"}):
            handlers = get_registered_handlers()
            assert "read_file" in handlers
            assert "web_fetch" in handlers


class TestToolCategorization:
    """Verify tool categorization is complete and correct."""

    def test_all_tools_categorized(self) -> None:
        all_tools = DEMO_TOOL_NAMES | PRODUCTION_TOOL_NAMES
        assert all_tools == {"read_file", "web_fetch", "calculate", "current_time", "echo"}

    def test_no_overlap_between_demo_and_production(self) -> None:
        assert not DEMO_TOOL_NAMES.intersection(PRODUCTION_TOOL_NAMES)

    def test_production_tools_are_pure_logic(self) -> None:
        """Production tools must not contain simulated I/O."""
        prod_tools = get_production_tools()
        for tool in prod_tools:
            assert tool.name not in DEMO_TOOL_NAMES

    def test_demo_tools_are_simulated(self) -> None:
        demo_tools = get_demo_tools()
        for tool in demo_tools:
            assert tool.name in DEMO_TOOL_NAMES
