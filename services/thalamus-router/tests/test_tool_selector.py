"""Unit tests for the ToolSelector."""

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.tool_selector import ToolSelector


class TestToolSelector:
    """Tests for tool selection logic."""

    def setup_method(self) -> None:
        """Create a fresh selector for each test."""
        self.selector = ToolSelector()

    def test_code_intent_tools(self) -> None:
        """Test that code intent includes code tools."""
        tools = self.selector.select("Write a function", IntentCategory.CODE)
        assert "code_execution" in tools
        assert "file_system" in tools

    def test_research_intent_tools(self) -> None:
        """Test that research intent includes search tools."""
        tools = self.selector.select("Find information", IntentCategory.RESEARCH)
        assert "web_search" in tools
        assert "knowledge_base" in tools

    def test_automation_intent_tools(self) -> None:
        """Test that automation intent includes workflow tools."""
        tools = self.selector.select("Automate this", IntentCategory.AUTOMATION)
        assert "workflow_engine" in tools
        assert "scheduler" in tools

    def test_memory_intent_tools(self) -> None:
        """Test that memory intent includes memory tool."""
        tools = self.selector.select("Remember this", IntentCategory.MEMORY)
        assert "memory_store" in tools

    def test_system_intent_tools(self) -> None:
        """Test that system intent includes admin tool."""
        tools = self.selector.select("Check status", IntentCategory.SYSTEM)
        assert "system_admin" in tools

    def test_chat_intent_no_default_tools(self) -> None:
        """Test that chat intent has no default tools."""
        tools = self.selector.select("Hello", IntentCategory.CHAT)
        assert tools == []

    def test_content_pattern_web_search(self) -> None:
        """Test that web search pattern adds tool."""
        tools = self.selector.select("search the web for info", IntentCategory.CHAT)
        assert "web_search" in tools

    def test_content_pattern_calculator(self) -> None:
        """Test that calculate pattern adds calculator tool."""
        tools = self.selector.select("calculate 2 + 3", IntentCategory.CHAT)
        assert "calculator" in tools

    def test_content_pattern_code_execution(self) -> None:
        """Test that run code pattern adds execution tool."""
        tools = self.selector.select("run the code please", IntentCategory.CHAT)
        assert "code_execution" in tools

    def test_returns_sorted_list(self) -> None:
        """Test that results are sorted."""
        tools = self.selector.select("Write a function", IntentCategory.CODE)
        assert tools == sorted(tools)

    def test_no_duplicates(self) -> None:
        """Test that tools list has no duplicates."""
        # Content pattern + intent both reference code_execution
        tools = self.selector.select("run the code and execute it", IntentCategory.CODE)
        assert len(tools) == len(set(tools))
