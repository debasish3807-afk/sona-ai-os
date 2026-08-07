"""Unit tests for the ContextBuilder."""

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.context_builder import ContextBuilder


class TestContextBuilder:
    """Tests for execution context building."""

    def setup_method(self) -> None:
        """Create a fresh builder for each test."""
        self.builder = ContextBuilder()

    def test_basic_context_building(self) -> None:
        """Test basic context extraction from request."""
        request = {
            "content": "Hello",
            "session_id": "sess-123",
            "user_id": "user-456",
            "context": {},
        }
        ctx = self.builder.build(request, IntentCategory.CHAT)
        assert ctx.session_id == "sess-123"
        assert ctx.user_id == "user-456"

    def test_memory_retrieval_for_memory_intent(self) -> None:
        """Test memory retrieval enabled for MEMORY intent."""
        request = {"content": "Recall something", "context": {}}
        ctx = self.builder.build(request, IntentCategory.MEMORY)
        assert ctx.needs_memory_retrieval is True

    def test_memory_retrieval_from_keywords(self) -> None:
        """Test memory retrieval enabled from content keywords."""
        request = {"content": "What did you remember from last time?", "context": {}}
        ctx = self.builder.build(request, IntentCategory.CHAT)
        assert ctx.needs_memory_retrieval is True

    def test_memory_retrieval_from_context_flag(self) -> None:
        """Test memory retrieval from explicit context flag."""
        request = {"content": "Hello", "context": {"include_memory": True}}
        ctx = self.builder.build(request, IntentCategory.CHAT)
        assert ctx.needs_memory_retrieval is True

    def test_knowledge_query_for_research(self) -> None:
        """Test knowledge query enabled for RESEARCH intent."""
        request = {"content": "Research AI trends", "context": {}}
        ctx = self.builder.build(request, IntentCategory.RESEARCH)
        assert ctx.needs_knowledge_query is True

    def test_knowledge_query_from_keywords(self) -> None:
        """Test knowledge query from content patterns."""
        request = {"content": "What is machine learning?", "context": {}}
        ctx = self.builder.build(request, IntentCategory.CHAT)
        assert ctx.needs_knowledge_query is True

    def test_token_budget_default(self) -> None:
        """Test default token budget for CHAT."""
        request = {"content": "Hello", "context": {}}
        ctx = self.builder.build(request, IntentCategory.CHAT)
        assert ctx.token_budget == 2048

    def test_token_budget_code(self) -> None:
        """Test increased token budget for CODE."""
        request = {"content": "Write a function", "context": {}}
        ctx = self.builder.build(request, IntentCategory.CODE)
        assert ctx.token_budget == 4096

    def test_token_budget_increases_with_content(self) -> None:
        """Test token budget increases for longer content."""
        long_content = " ".join(["word"] * 60)
        request = {"content": long_content, "context": {}}
        ctx = self.builder.build(request, IntentCategory.CODE)
        assert ctx.token_budget > 4096

    def test_user_preferences_extracted(self) -> None:
        """Test user preferences extraction from context."""
        request = {
            "content": "Hello",
            "context": {
                "language": "python",
                "response_format": "markdown",
                "temperature": 0.8,
            },
        }
        ctx = self.builder.build(request, IntentCategory.CHAT)
        assert ctx.user_preferences["language"] == "python"
        assert ctx.user_preferences["response_format"] == "markdown"
        assert ctx.user_preferences["temperature"] == 0.8

    def test_history_depth_default(self) -> None:
        """Test default history depth."""
        request = {"content": "Hello", "context": {}}
        ctx = self.builder.build(request, IntentCategory.CHAT)
        assert ctx.history_depth == 5

    def test_history_depth_memory(self) -> None:
        """Test increased history for MEMORY intent."""
        request = {"content": "Recall", "context": {}}
        ctx = self.builder.build(request, IntentCategory.MEMORY)
        assert ctx.history_depth == 10

    def test_history_depth_system(self) -> None:
        """Test minimal history for SYSTEM intent."""
        request = {"content": "Status", "context": {}}
        ctx = self.builder.build(request, IntentCategory.SYSTEM)
        assert ctx.history_depth == 0

    def test_history_depth_override(self) -> None:
        """Test explicit history depth override."""
        request = {"content": "Hello", "context": {"history_depth": 20}}
        ctx = self.builder.build(request, IntentCategory.CHAT)
        assert ctx.history_depth == 20
