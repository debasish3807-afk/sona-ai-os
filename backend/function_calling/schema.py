"""Tool schema generation for LLM function calling.

Converts the internal ToolMetadata format into the OpenAI-compatible
function calling schema that all major providers support.
"""

from __future__ import annotations

from typing import Any

from tools.base import ToolMetadata, ToolParam


def _param_to_json_schema(param: ToolParam) -> dict[str, Any]:
    """Convert a ToolParam to JSON Schema property."""
    type_map: dict[str, str] = {
        "string": "string",
        "integer": "integer",
        "boolean": "boolean",
        "array": "array",
        "object": "object",
        "number": "number",
    }
    schema: dict[str, Any] = {
        "type": type_map.get(param.param_type, "string"),
        "description": param.description,
    }
    if param.default is not None:
        schema["default"] = param.default
    return schema


def tool_to_function_schema(metadata: ToolMetadata) -> dict[str, Any]:
    """Convert ToolMetadata to OpenAI function calling schema.

    Args:
        metadata: The tool's metadata.

    Returns:
        Function schema dict compatible with OpenAI/Claude/Gemini.
    """
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in metadata.parameters:
        properties[param.name] = _param_to_json_schema(param)
        if param.required:
            required.append(param.name)

    return {
        "type": "function",
        "function": {
            "name": metadata.name,
            "description": metadata.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def generate_tool_schemas(
    tools: list[ToolMetadata],
    exclude_dangerous: bool = False,
) -> list[dict[str, Any]]:
    """Generate function calling schemas for a list of tools.

    Args:
        tools: List of tool metadata.
        exclude_dangerous: Skip dangerous tools.

    Returns:
        List of OpenAI-compatible function schemas.
    """
    schemas: list[dict[str, Any]] = []
    for meta in tools:
        if exclude_dangerous and meta.dangerous:
            continue
        schemas.append(tool_to_function_schema(meta))
    return schemas
