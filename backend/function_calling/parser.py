"""Function call parsing — extracts tool calls from LLM responses.

Handles the various formats that different providers use to express
function/tool calls and normalizes them into a unified FunctionCall.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FunctionCall:
    """A parsed function/tool call from an LLM response."""

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str = ""

    def validate_against(self, required_params: list[str]) -> list[str]:
        """Check that required parameters are present.

        Returns:
            List of missing parameter names.
        """
        return [p for p in required_params if p not in self.arguments]


def parse_function_call(tool_call_data: dict[str, Any]) -> FunctionCall | None:
    """Parse a function call from provider response data.

    Handles OpenAI, Claude, and Gemini formats.

    Args:
        tool_call_data: Raw tool call dictionary from LLM.

    Returns:
        Parsed FunctionCall or None if parsing fails.
    """
    # OpenAI format: {"id": "...", "function": {"name": "...", "arguments": "{...}"}}
    if "function" in tool_call_data:
        func = tool_call_data["function"]
        name = func.get("name", "")
        args_raw = func.get("arguments", "{}")
        call_id = tool_call_data.get("id", "")

        try:
            arguments = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
        except json.JSONDecodeError:
            logger.warning("Failed to parse function arguments", raw=args_raw[:200])
            arguments = {}

        if name:
            return FunctionCall(name=name, arguments=arguments, call_id=call_id)

    # Claude format: {"type": "tool_use", "name": "...", "input": {...}}
    if tool_call_data.get("type") == "tool_use":
        name = tool_call_data.get("name", "")
        arguments = tool_call_data.get("input", {})
        call_id = tool_call_data.get("id", "")
        if name:
            return FunctionCall(name=name, arguments=arguments, call_id=call_id)

    # Gemini format: {"functionCall": {"name": "...", "args": {...}}}
    if "functionCall" in tool_call_data:
        fc = tool_call_data["functionCall"]
        name = fc.get("name", "")
        arguments = fc.get("args", {})
        if name:
            return FunctionCall(name=name, arguments=arguments)

    # Direct format: {"name": "...", "arguments": {...}}
    name = tool_call_data.get("name", "")
    if name:
        arguments = tool_call_data.get("arguments", tool_call_data.get("params", {}))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        return FunctionCall(name=name, arguments=arguments)

    logger.debug("Could not parse function call", data=str(tool_call_data)[:200])
    return None


def parse_multiple_calls(
    tool_calls: list[dict[str, Any]],
) -> list[FunctionCall]:
    """Parse multiple function calls from an LLM response.

    Args:
        tool_calls: List of raw tool call dictionaries.

    Returns:
        List of successfully parsed FunctionCalls.
    """
    results: list[FunctionCall] = []
    for call_data in tool_calls:
        parsed = parse_function_call(call_data)
        if parsed:
            results.append(parsed)
    return results
