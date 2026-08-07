"""Built-in tools for MCP Integration.

Provides functional built-in tools for testing and basic operations:
- read_file: Reads file content (simulated filesystem)
- web_fetch: Fetches URL content (simulated)
- calculate: Basic math evaluation
- current_time: Returns current timestamp
- echo: Returns input as output
"""

import ast
import math
import operator
import time
from datetime import UTC, datetime
from typing import Any

import structlog

from sona_mcp.domain.models import MCPServer, MCPTool, MCPTransport, ToolPermission

logger = structlog.get_logger()


# Simulated filesystem for read_file tool
_SIMULATED_FS: dict[str, str] = {
    "/tmp/hello.txt": "Hello, World!",
    "/tmp/data.json": '{"key": "value", "count": 42}',
    "/tmp/config.yaml": "name: sona\nversion: 1.0\n",
    "/tmp/notes.md": "# Notes\n\n- Item one\n- Item two\n",
}


async def handle_read_file(arguments: dict[str, Any]) -> dict[str, Any]:
    """Read file content from simulated filesystem.

    Args:
        arguments: Must contain 'path' key with the file path.

    Returns:
        Dict with 'content' and 'path' keys.
    """
    path = arguments.get("path", "")
    if not path:
        raise ValueError("Missing required argument: 'path'")

    content = _SIMULATED_FS.get(path)
    if content is None:
        raise FileNotFoundError(f"File not found: {path}")

    return {"path": path, "content": content}


async def handle_web_fetch(arguments: dict[str, Any]) -> dict[str, Any]:
    """Fetch URL content (simulated).

    Args:
        arguments: Must contain 'url' key.

    Returns:
        Dict with 'url', 'status', and 'content' keys.
    """
    url = arguments.get("url", "")
    if not url:
        raise ValueError("Missing required argument: 'url'")

    # Simulated responses
    simulated_responses: dict[str, dict[str, Any]] = {
        "https://api.example.com/data": {
            "status": 200,
            "content": '{"message": "OK", "data": [1, 2, 3]}',
        },
        "https://example.com": {
            "status": 200,
            "content": "<html><body>Example Domain</body></html>",
        },
    }

    response = simulated_responses.get(url, {"status": 404, "content": "Not Found"})
    return {"url": url, **response}


# Safe operators for the calculate tool
_SAFE_OPERATORS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCTIONS: dict[str, Any] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval_node(node: ast.AST) -> Any:
    """Safely evaluate an AST node for math expressions."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.BinOp):
        op_func = _SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        return op_func(left, right)
    if isinstance(node, ast.UnaryOp):
        op_func = _SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(_safe_eval_node(node.operand))
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func = _SAFE_FUNCTIONS.get(node.func.id)
            if func is None:
                raise ValueError(f"Unsupported function: {node.func.id}")
            args = [_safe_eval_node(arg) for arg in node.args]
            return func(*args)
        raise ValueError("Complex function calls not supported")
    if isinstance(node, ast.Name):
        val = _SAFE_FUNCTIONS.get(node.id)
        if val is None:
            raise ValueError(f"Unsupported name: {node.id}")
        return val
    raise ValueError(f"Unsupported expression type: {type(node).__name__}")


async def handle_calculate(arguments: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a mathematical expression safely.

    Args:
        arguments: Must contain 'expression' key with a math expression.

    Returns:
        Dict with 'expression' and 'result' keys.
    """
    expression = arguments.get("expression", "")
    if not expression:
        raise ValueError("Missing required argument: 'expression'")

    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval_node(tree)
        return {"expression": expression, "result": result}
    except (SyntaxError, ValueError, ZeroDivisionError, TypeError) as e:
        raise ValueError(f"Invalid expression: {e!s}") from e


async def handle_current_time(arguments: dict[str, Any]) -> dict[str, Any]:
    """Return the current timestamp.

    Args:
        arguments: Optional 'format' key for datetime format string.

    Returns:
        Dict with 'timestamp', 'iso', and 'unix' keys.
    """
    now = datetime.now(UTC)
    fmt = arguments.get("format", "%Y-%m-%d %H:%M:%S %Z")
    return {
        "timestamp": now.strftime(fmt),
        "iso": now.isoformat(),
        "unix": time.time(),
    }


async def handle_echo(arguments: dict[str, Any]) -> dict[str, Any]:
    """Echo back the input.

    Args:
        arguments: Must contain 'message' key.

    Returns:
        Dict with 'message' key echoed back.
    """
    message = arguments.get("message", "")
    return {"message": message}


# Built-in tool definitions
BUILTIN_TOOLS: list[MCPTool] = [
    MCPTool(
        name="read_file",
        description="Reads file content from the filesystem",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        permissions=[ToolPermission.READ],
        server_id="builtin",
    ),
    MCPTool(
        name="web_fetch",
        description="Fetches content from a URL",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
        permissions=[ToolPermission.READ],
        server_id="builtin",
    ),
    MCPTool(
        name="calculate",
        description="Evaluates a mathematical expression",
        input_schema={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
        permissions=[ToolPermission.READ],
        server_id="builtin",
    ),
    MCPTool(
        name="current_time",
        description="Returns the current timestamp",
        input_schema={
            "type": "object",
            "properties": {"format": {"type": "string"}},
        },
        permissions=[ToolPermission.READ],
        server_id="builtin",
    ),
    MCPTool(
        name="echo",
        description="Returns the input message as output",
        input_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
        },
        permissions=[ToolPermission.READ],
        server_id="builtin",
    ),
]

BUILTIN_SERVER = MCPServer(
    server_id="builtin",
    name="Built-in Tools",
    transport=MCPTransport.STDIO,
    tools=BUILTIN_TOOLS,
)

# Handler registry for built-in tools
BUILTIN_HANDLERS: dict[str, Any] = {
    "read_file": handle_read_file,
    "web_fetch": handle_web_fetch,
    "calculate": handle_calculate,
    "current_time": handle_current_time,
    "echo": handle_echo,
}
