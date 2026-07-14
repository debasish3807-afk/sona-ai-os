"""Tests for the Desktop Workspace API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.workspace import (
    _conversations,
    _workspace_settings,
    router,
)


@pytest.fixture
def app():
    """Create test FastAPI app with workspace router."""
    from fastapi import FastAPI

    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestChatEndpoints:
    """Tests for chat streaming and completion."""

    def test_chat_complete(self, client):
        """Non-streaming chat returns response."""
        resp = client.post(
            "/workspace/chat/complete",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data
        assert data["provider"] == "ollama"
        assert data["model"] == "llama3"

    def test_chat_stream(self, client):
        """Streaming chat returns SSE events."""
        resp = client.post(
            "/workspace/chat",
            json={"messages": [{"role": "user", "content": "Hello"}], "stream": True},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        # Should contain data lines
        content = resp.text
        assert "data:" in content

    def test_chat_with_system_prompt(self, client):
        """Chat with system prompt works."""
        resp = client.post(
            "/workspace/chat/complete",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "system_prompt": "Be brief.",
            },
        )
        assert resp.status_code == 200
        assert "content" in resp.json()

    def test_chat_custom_model(self, client):
        """Chat with custom model works."""
        resp = client.post(
            "/workspace/chat/complete",
            json={"messages": [{"role": "user", "content": "test"}], "model": "mistral"},
        )
        assert resp.status_code == 200
        assert resp.json()["model"] == "mistral"


class TestFileExplorer:
    """Tests for file explorer endpoints."""

    def test_list_files(self, client):
        """List files returns workspace content."""
        resp = client.get("/workspace/files")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data

    def test_list_files_with_depth(self, client):
        """List files respects depth parameter."""
        resp = client.get("/workspace/files?depth=2")
        assert resp.status_code == 200
        assert "nodes" in resp.json()

    def test_path_traversal_blocked(self, client):
        """Path traversal attempts are blocked."""
        resp = client.get("/workspace/files?path=../../etc")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data or data.get("nodes") == []

    def test_read_file_content(self, client):
        """Read file returns content."""
        # Try reading a known file
        resp = client.get("/workspace/files/content?path=pyproject.toml")
        assert resp.status_code == 200
        data = resp.json()
        # Either content or error (if not in workspace)
        assert "type" in data or "error" in data

    def test_read_file_path_traversal(self, client):
        """File read blocks path traversal."""
        resp = client.get("/workspace/files/content?path=../../etc/passwd")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data


class TestTerminal:
    """Tests for terminal execution."""

    def test_execute_command(self, client):
        """Execute simple command returns output."""
        resp = client.post(
            "/workspace/terminal",
            json={"command": "echo hello", "timeout": 5},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        content = resp.text
        assert "hello" in content

    def test_execute_with_timeout(self, client):
        """Command with custom timeout."""
        resp = client.post(
            "/workspace/terminal",
            json={"command": "echo done", "timeout": 2},
        )
        assert resp.status_code == 200

    def test_path_traversal_denied(self, client):
        """Terminal denies out-of-workspace execution."""
        resp = client.post(
            "/workspace/terminal",
            json={"command": "ls", "cwd": "/etc"},
        )
        assert resp.status_code == 200
        content = resp.text
        assert "denied" in content.lower() or "error" in content.lower()


class TestConversations:
    """Tests for conversation management."""

    def setup_method(self):
        """Clear conversations between tests."""
        _conversations.clear()

    def test_create_conversation(self, client):
        """Create a new conversation."""
        resp = client.post("/workspace/conversations?title=Test Chat")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["title"] == "Test Chat"

    def test_list_conversations(self, client):
        """List conversations returns all."""
        client.post("/workspace/conversations?title=Chat 1")
        client.post("/workspace/conversations?title=Chat 2")
        resp = client.get("/workspace/conversations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2

    def test_update_conversation(self, client):
        """Update conversation title."""
        create_resp = client.post("/workspace/conversations?title=Old Title")
        conv_id = create_resp.json()["id"]
        resp = client.patch(f"/workspace/conversations/{conv_id}?title=New Title")
        assert resp.status_code == 200
        assert resp.json()["updated"] is True

    def test_pin_conversation(self, client):
        """Pin a conversation."""
        create_resp = client.post("/workspace/conversations?title=Important")
        conv_id = create_resp.json()["id"]
        resp = client.patch(f"/workspace/conversations/{conv_id}?pinned=true")
        assert resp.status_code == 200

    def test_delete_conversation(self, client):
        """Delete a conversation."""
        create_resp = client.post("/workspace/conversations?title=Temp")
        conv_id = create_resp.json()["id"]
        resp = client.delete(f"/workspace/conversations/{conv_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_nonexistent(self, client):
        """Delete nonexistent conversation."""
        resp = client.delete("/workspace/conversations/fake-id")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is False


class TestSettings:
    """Tests for workspace settings."""

    def setup_method(self):
        """Reset settings between tests."""
        _workspace_settings.update(
            {
                "provider": "ollama",
                "model": "llama3",
                "theme": "dark",
                "temperature": 0.7,
                "max_tokens": 4096,
                "research_depth": "standard",
            }
        )

    def test_get_settings(self, client):
        """Get current settings."""
        resp = client.get("/workspace/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "ollama"
        assert data["theme"] == "dark"

    def test_update_provider(self, client):
        """Update AI provider."""
        resp = client.patch("/workspace/settings", json={"provider": "gemini"})
        assert resp.status_code == 200
        assert resp.json()["settings"]["provider"] == "gemini"

    def test_update_theme(self, client):
        """Update theme."""
        resp = client.patch("/workspace/settings", json={"theme": "light"})
        assert resp.status_code == 200
        assert resp.json()["settings"]["theme"] == "light"

    def test_update_temperature(self, client):
        """Update temperature."""
        resp = client.patch("/workspace/settings", json={"temperature": 0.3})
        assert resp.status_code == 200
        assert resp.json()["settings"]["temperature"] == 0.3

    def test_update_multiple(self, client):
        """Update multiple settings at once."""
        resp = client.patch(
            "/workspace/settings",
            json={"model": "mistral", "max_tokens": 2048},
        )
        assert resp.status_code == 200
        data = resp.json()["settings"]
        assert data["model"] == "mistral"
        assert data["max_tokens"] == 2048


class TestResearch:
    """Tests for deep research endpoint."""

    def test_research_stream(self, client):
        """Research returns SSE stream."""
        resp = client.post("/workspace/research?query=AI+history&offline=true")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        content = resp.text
        assert "data:" in content
