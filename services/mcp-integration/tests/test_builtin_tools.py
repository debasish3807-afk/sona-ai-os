"""Unit tests for built-in tools."""

import pytest

from sona_mcp.infrastructure.builtin_tools import (
    BUILTIN_HANDLERS,
    BUILTIN_SERVER,
    BUILTIN_TOOLS,
    handle_calculate,
    handle_current_time,
    handle_echo,
    handle_read_file,
    handle_web_fetch,
)


class TestBuiltinToolDefinitions:
    def test_five_builtin_tools(self) -> None:
        assert len(BUILTIN_TOOLS) == 5

    def test_builtin_server_exists(self) -> None:
        assert BUILTIN_SERVER.server_id == "builtin"
        assert BUILTIN_SERVER.name == "Built-in Tools"
        assert len(BUILTIN_SERVER.tools) == 5

    def test_all_handlers_registered(self) -> None:
        assert "read_file" in BUILTIN_HANDLERS
        assert "web_fetch" in BUILTIN_HANDLERS
        assert "calculate" in BUILTIN_HANDLERS
        assert "current_time" in BUILTIN_HANDLERS
        assert "echo" in BUILTIN_HANDLERS

    def test_tool_names_match_handlers(self) -> None:
        tool_names = {t.name for t in BUILTIN_TOOLS}
        handler_names = set(BUILTIN_HANDLERS.keys())
        assert tool_names == handler_names


class TestReadFile:
    @pytest.mark.asyncio
    async def test_read_existing_file(self) -> None:
        result = await handle_read_file({"path": "/tmp/hello.txt"})
        assert result["content"] == "Hello, World!"
        assert result["path"] == "/tmp/hello.txt"

    @pytest.mark.asyncio
    async def test_read_json_file(self) -> None:
        result = await handle_read_file({"path": "/tmp/data.json"})
        assert "key" in result["content"]

    @pytest.mark.asyncio
    async def test_read_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            await handle_read_file({"path": "/nonexistent"})

    @pytest.mark.asyncio
    async def test_read_no_path(self) -> None:
        with pytest.raises(ValueError, match="path"):
            await handle_read_file({})

    @pytest.mark.asyncio
    async def test_read_empty_path(self) -> None:
        with pytest.raises(ValueError, match="path"):
            await handle_read_file({"path": ""})


class TestWebFetch:
    @pytest.mark.asyncio
    async def test_fetch_known_url(self) -> None:
        result = await handle_web_fetch({"url": "https://example.com"})
        assert result["status"] == 200
        assert "Example" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_api_url(self) -> None:
        result = await handle_web_fetch({"url": "https://api.example.com/data"})
        assert result["status"] == 200
        assert "message" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_unknown_url(self) -> None:
        result = await handle_web_fetch({"url": "https://unknown.example.com"})
        assert result["status"] == 404

    @pytest.mark.asyncio
    async def test_fetch_no_url(self) -> None:
        with pytest.raises(ValueError, match="url"):
            await handle_web_fetch({})

    @pytest.mark.asyncio
    async def test_fetch_empty_url(self) -> None:
        with pytest.raises(ValueError, match="url"):
            await handle_web_fetch({"url": ""})


class TestCalculate:
    @pytest.mark.asyncio
    async def test_addition(self) -> None:
        result = await handle_calculate({"expression": "2 + 3"})
        assert result["result"] == 5

    @pytest.mark.asyncio
    async def test_multiplication(self) -> None:
        result = await handle_calculate({"expression": "6 * 7"})
        assert result["result"] == 42

    @pytest.mark.asyncio
    async def test_division(self) -> None:
        result = await handle_calculate({"expression": "10 / 4"})
        assert result["result"] == 2.5

    @pytest.mark.asyncio
    async def test_power(self) -> None:
        result = await handle_calculate({"expression": "2 ** 10"})
        assert result["result"] == 1024

    @pytest.mark.asyncio
    async def test_complex_expression(self) -> None:
        result = await handle_calculate({"expression": "(3 + 4) * 2"})
        assert result["result"] == 14

    @pytest.mark.asyncio
    async def test_negative_number(self) -> None:
        result = await handle_calculate({"expression": "-5 + 3"})
        assert result["result"] == -2

    @pytest.mark.asyncio
    async def test_sqrt_function(self) -> None:
        result = await handle_calculate({"expression": "sqrt(16)"})
        assert result["result"] == 4.0

    @pytest.mark.asyncio
    async def test_invalid_expression(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            await handle_calculate({"expression": "import os"})

    @pytest.mark.asyncio
    async def test_division_by_zero(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            await handle_calculate({"expression": "1 / 0"})

    @pytest.mark.asyncio
    async def test_no_expression(self) -> None:
        with pytest.raises(ValueError, match="expression"):
            await handle_calculate({})

    @pytest.mark.asyncio
    async def test_floor_division(self) -> None:
        result = await handle_calculate({"expression": "7 // 2"})
        assert result["result"] == 3

    @pytest.mark.asyncio
    async def test_modulo(self) -> None:
        result = await handle_calculate({"expression": "10 % 3"})
        assert result["result"] == 1


class TestCurrentTime:
    @pytest.mark.asyncio
    async def test_returns_timestamp(self) -> None:
        result = await handle_current_time({})
        assert "timestamp" in result
        assert "iso" in result
        assert "unix" in result

    @pytest.mark.asyncio
    async def test_unix_is_number(self) -> None:
        result = await handle_current_time({})
        assert isinstance(result["unix"], float)

    @pytest.mark.asyncio
    async def test_iso_format(self) -> None:
        result = await handle_current_time({})
        assert "T" in result["iso"]  # ISO format includes T separator

    @pytest.mark.asyncio
    async def test_custom_format(self) -> None:
        result = await handle_current_time({"format": "%Y"})
        assert len(result["timestamp"]) == 4  # Just the year


class TestEcho:
    @pytest.mark.asyncio
    async def test_echo_message(self) -> None:
        result = await handle_echo({"message": "hello"})
        assert result["message"] == "hello"

    @pytest.mark.asyncio
    async def test_echo_empty(self) -> None:
        result = await handle_echo({})
        assert result["message"] == ""

    @pytest.mark.asyncio
    async def test_echo_special_chars(self) -> None:
        msg = "Hello <World> & 'Friends'"
        result = await handle_echo({"message": msg})
        assert result["message"] == msg
