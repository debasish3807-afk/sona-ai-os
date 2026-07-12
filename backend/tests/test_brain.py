"""Brain module tests — validates AI Brain execution pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBrainSchemas:
    """Test Brain request/response schemas."""

    def test_chat_message_schema(self):
        """ChatMessageSchema validates correctly."""
        from brain.schemas import ChatMessageSchema

        msg = ChatMessageSchema(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_chat_endpoint_request(self):
        """ChatEndpointRequest with defaults."""
        from brain.schemas import ChatEndpointRequest, ChatMessageSchema

        req = ChatEndpointRequest(messages=[ChatMessageSchema(role="user", content="Hi")])
        assert req.temperature == 0.7
        assert req.max_tokens == 4096
        assert req.stream is False
        assert req.model is None
        assert req.provider is None

    def test_chat_endpoint_response(self):
        """ChatEndpointResponse construction."""
        from brain.schemas import ChatEndpointResponse, TokenUsageSchema

        resp = ChatEndpointResponse(
            response_id="test-123",
            content="Hello there!",
            model="llama3",
            provider="ollama",
            agent="general",
            token_usage=TokenUsageSchema(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            latency_ms=100.0,
        )
        assert resp.success is True
        assert resp.content == "Hello there!"
        assert resp.token_usage.total_tokens == 15

    def test_brain_request(self):
        """BrainRequest construction."""
        from brain.schemas import BrainRequest, ChatMessageSchema

        req = BrainRequest(
            messages=[ChatMessageSchema(role="user", content="Test")],
            model="llama3",
            session_id="sess-1",
        )
        assert req.model == "llama3"
        assert req.session_id == "sess-1"

    def test_brain_stream_chunk(self):
        """BrainStreamChunk construction."""
        from brain.schemas import BrainStreamChunk

        chunk = BrainStreamChunk(event="delta", content="Hello", model="llama3")
        assert chunk.event == "delta"
        assert chunk.content == "Hello"


class TestAgentRouter:
    """Test agent routing logic."""

    def test_general_routing_short_message(self):
        """Short messages route to general agent."""
        from brain.agent_router import AgentCategory, detect_agent
        from brain.schemas import ChatMessageSchema

        messages = [ChatMessageSchema(role="user", content="Hello")]
        assert detect_agent(messages) == AgentCategory.GENERAL

    def test_coding_routing(self):
        """Code-related messages route to coding agent."""
        from brain.agent_router import AgentCategory, detect_agent
        from brain.schemas import ChatMessageSchema

        messages = [
            ChatMessageSchema(
                role="user",
                content="Write a Python function to implement a binary search algorithm",
            )
        ]
        assert detect_agent(messages) == AgentCategory.CODING

    def test_research_routing(self):
        """Research-related messages route to research agent."""
        from brain.agent_router import AgentCategory, detect_agent
        from brain.schemas import ChatMessageSchema

        messages = [
            ChatMessageSchema(
                role="user",
                content="Research and compare the pros and cons of different database systems, summarize your analysis",
            )
        ]
        assert detect_agent(messages) == AgentCategory.RESEARCH

    def test_planner_routing(self):
        """Planning-related messages route to planner agent."""
        from brain.agent_router import AgentCategory, detect_agent
        from brain.schemas import ChatMessageSchema

        messages = [
            ChatMessageSchema(
                role="user",
                content="Create a project plan with timeline and milestones for the sprint",
            )
        ]
        assert detect_agent(messages) == AgentCategory.PLANNER

    def test_android_routing(self):
        """Android-related messages route to android agent."""
        from brain.agent_router import AgentCategory, detect_agent
        from brain.schemas import ChatMessageSchema

        messages = [
            ChatMessageSchema(
                role="user",
                content="Build an Android activity using Jetpack Compose with a ViewModel and Room database",
            )
        ]
        assert detect_agent(messages) == AgentCategory.ANDROID

    def test_agent_system_prompt(self):
        """Agent system prompts are returned for specialized agents."""
        from brain.agent_router import AgentCategory, get_agent_system_prompt

        prompt = get_agent_system_prompt(AgentCategory.CODING)
        assert prompt is not None
        assert "Coding Agent" in prompt

        general_prompt = get_agent_system_prompt(AgentCategory.GENERAL)
        assert general_prompt is None


class TestMemoryBridge:
    """Test memory bridge integration."""

    def test_save_and_retrieve(self):
        """Messages can be saved and retrieved."""
        from brain.memory_bridge import (
            _conversation_store,
            retrieve_conversation_history,
            save_message_to_memory,
        )

        session = "test-session-memory"
        _conversation_store.pop(session, None)  # Clean slate

        save_message_to_memory(session, "user", "Hello Brain")
        save_message_to_memory(session, "assistant", "Hello User")

        history = retrieve_conversation_history(session)
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello Brain"
        assert history[1].role == "assistant"

        _conversation_store.pop(session, None)  # Cleanup

    def test_retrieve_empty_session(self):
        """Empty session returns empty history."""
        from brain.memory_bridge import retrieve_conversation_history

        history = retrieve_conversation_history("nonexistent-session")
        assert history == []

    def test_retrieve_no_session(self):
        """None session returns empty history."""
        from brain.memory_bridge import retrieve_conversation_history

        history = retrieve_conversation_history(None)
        assert history == []

    def test_build_context_with_system_prompt(self):
        """Context builder includes system prompt."""
        from brain.memory_bridge import build_context_messages
        from brain.schemas import ChatMessageSchema

        messages = [ChatMessageSchema(role="user", content="Hi")]
        result = build_context_messages(
            request_messages=messages,
            history=[],
            system_prompt="You are a test bot",
        )
        assert result[0].role == "system"
        assert "test bot" in result[0].content
        assert result[-1].role == "user"

    def test_build_context_default_system_prompt(self):
        """Context builder adds default system prompt when none provided."""
        from brain.memory_bridge import build_context_messages
        from brain.schemas import ChatMessageSchema

        messages = [ChatMessageSchema(role="user", content="Hi")]
        result = build_context_messages(request_messages=messages, history=[], system_prompt=None)
        assert result[0].role == "system"
        assert "Sona" in result[0].content

    def test_session_stats(self):
        """Session stats are computed correctly."""
        from brain.memory_bridge import (
            _conversation_store,
            get_session_stats,
            save_message_to_memory,
        )

        session = "test-session-stats"
        _conversation_store.pop(session, None)

        save_message_to_memory(session, "user", "msg1")
        save_message_to_memory(session, "assistant", "msg2")
        save_message_to_memory(session, "user", "msg3")

        stats = get_session_stats(session)
        assert stats["total_messages"] == 3
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 1

        _conversation_store.pop(session, None)


class TestOllamaProvider:
    """Test Ollama provider initialization and properties."""

    def test_provider_creation(self):
        """OllamaProvider can be instantiated."""
        from providers.ollama_provider import OllamaProvider

        provider = OllamaProvider()
        assert provider.provider_id.value == "ollama"
        assert provider.display_name == "Ollama (Local)"
        assert provider.is_initialized is False

    def test_provider_supports_streaming(self):
        """OllamaProvider supports streaming."""
        from providers.ollama_provider import OllamaProvider

        provider = OllamaProvider()
        assert provider.supports_streaming() is True
        assert provider.supports_tools() is False
        assert provider.supports_vision() is False

    def test_provider_config_defaults(self):
        """OllamaProvider uses correct default config."""
        from providers.ollama_provider import OllamaProvider

        provider = OllamaProvider()
        assert "localhost:11434" in provider.base_url
        assert provider.config.default_model == "llama3"


class TestBrainOrchestrator:
    """Test Brain orchestrator setup."""

    def test_orchestrator_creation(self):
        """BrainOrchestrator can be instantiated."""
        from brain.orchestrator import BrainOrchestrator

        brain = BrainOrchestrator()
        assert brain.is_initialized is False
        assert brain.available_providers == {}

    def test_get_brain_singleton(self):
        """get_brain returns consistent instance."""
        from brain.orchestrator import get_brain

        brain1 = get_brain()
        brain2 = get_brain()
        assert brain1 is brain2
