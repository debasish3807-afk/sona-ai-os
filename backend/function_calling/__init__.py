"""Function Calling — provider-independent tool invocation via LLM.

Generates tool schemas compatible with all providers, parses
LLM function call responses, and validates arguments.
"""

from function_calling.parser import FunctionCall, parse_function_call
from function_calling.schema import generate_tool_schemas

__all__ = [
    "FunctionCall",
    "generate_tool_schemas",
    "parse_function_call",
]
