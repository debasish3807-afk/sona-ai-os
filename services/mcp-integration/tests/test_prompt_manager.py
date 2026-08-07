"""Unit tests for PromptManager."""

import pytest

from sona_mcp.infrastructure.prompt_manager import MCPPrompt, PromptManager


def _make_prompt(
    name: str = "summarize",
    template: str = "Summarize: {text}",
    server_id: str = "srv-1",
) -> MCPPrompt:
    return MCPPrompt(
        name=name,
        description="Summarize text",
        arguments=[{"name": "text", "required": True}],
        template=template,
        server_id=server_id,
    )


class TestPromptRegistration:
    @pytest.mark.asyncio
    async def test_register_prompt(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(_make_prompt())
        assert mgr.prompt_count == 1

    @pytest.mark.asyncio
    async def test_register_multiple(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(_make_prompt("p1"))
        await mgr.register_prompt(_make_prompt("p2"))
        assert mgr.prompt_count == 2

    @pytest.mark.asyncio
    async def test_unregister_prompt(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(_make_prompt())
        result = await mgr.unregister_prompt("summarize")
        assert result is True
        assert mgr.prompt_count == 0

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self) -> None:
        mgr = PromptManager()
        result = await mgr.unregister_prompt("missing")
        assert result is False


class TestPromptLookup:
    @pytest.mark.asyncio
    async def test_get_prompt(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(_make_prompt())
        prompt = await mgr.get_prompt("summarize")
        assert prompt is not None
        assert prompt.name == "summarize"

    @pytest.mark.asyncio
    async def test_get_missing(self) -> None:
        mgr = PromptManager()
        prompt = await mgr.get_prompt("missing")
        assert prompt is None

    @pytest.mark.asyncio
    async def test_list_all(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(_make_prompt("p1"))
        await mgr.register_prompt(_make_prompt("p2"))
        prompts = await mgr.list_prompts()
        assert len(prompts) == 2

    @pytest.mark.asyncio
    async def test_list_by_server(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(_make_prompt("p1", server_id="s1"))
        await mgr.register_prompt(_make_prompt("p2", server_id="s2"))
        s1_prompts = await mgr.list_prompts(server_id="s1")
        assert len(s1_prompts) == 1
        assert s1_prompts[0].name == "p1"


class TestPromptRendering:
    @pytest.mark.asyncio
    async def test_render_with_args(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(_make_prompt())
        result = await mgr.render_prompt("summarize", {"text": "Hello world"})
        assert result == "Summarize: Hello world"

    @pytest.mark.asyncio
    async def test_render_multiple_args(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(
            MCPPrompt(
                name="greet",
                template="Hello {name}, you are {age} years old",
                server_id="s1",
            )
        )
        result = await mgr.render_prompt("greet", {"name": "Alice", "age": "30"})
        assert result == "Hello Alice, you are 30 years old"

    @pytest.mark.asyncio
    async def test_render_no_args(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(MCPPrompt(name="static", template="Hello World", server_id="s1"))
        result = await mgr.render_prompt("static")
        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_render_missing_prompt(self) -> None:
        mgr = PromptManager()
        result = await mgr.render_prompt("missing")
        assert result is None


class TestPromptServerCleanup:
    @pytest.mark.asyncio
    async def test_remove_server_prompts(self) -> None:
        mgr = PromptManager()
        await mgr.register_prompt(_make_prompt("p1", server_id="s1"))
        await mgr.register_prompt(_make_prompt("p2", server_id="s1"))
        await mgr.register_prompt(_make_prompt("p3", server_id="s2"))
        removed = await mgr.remove_server_prompts("s1")
        assert removed == 2
        assert mgr.prompt_count == 1
