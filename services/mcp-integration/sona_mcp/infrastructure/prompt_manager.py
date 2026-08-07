"""Prompt manager for MCP Integration.

Manages MCP prompts (templates) exposed by servers.
Provides listing, retrieval, and rendering with arguments.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class MCPPrompt:
    """Represents a prompt template exposed by an MCP server.

    Attributes:
        name: Unique name of the prompt.
        description: Human-readable description.
        arguments: List of argument definitions.
        template: The prompt template string.
        server_id: ID of the server exposing this prompt.
    """

    name: str
    description: str = ""
    arguments: list[dict[str, Any]] = field(default_factory=list)
    template: str = ""
    server_id: str = ""


class PromptManager:
    """Manages MCP prompts with listing, retrieval, and rendering.

    Provides a centralized registry of prompt templates available
    across all connected MCP servers.
    """

    def __init__(self) -> None:
        """Initialize the prompt manager."""
        self._prompts: dict[str, MCPPrompt] = {}
        self._server_prompts: dict[str, set[str]] = {}

    async def register_prompt(self, prompt: MCPPrompt) -> None:
        """Register a prompt template.

        Args:
            prompt: The MCPPrompt to register.
        """
        self._prompts[prompt.name] = prompt
        if prompt.server_id not in self._server_prompts:
            self._server_prompts[prompt.server_id] = set()
        self._server_prompts[prompt.server_id].add(prompt.name)
        await logger.ainfo(
            "prompt_registered",
            name=prompt.name,
            server_id=prompt.server_id,
        )

    async def unregister_prompt(self, name: str) -> bool:
        """Remove a prompt from the manager.

        Args:
            name: The prompt name to remove.

        Returns:
            True if removed, False if not found.
        """
        prompt = self._prompts.pop(name, None)
        if prompt is None:
            return False
        if prompt.server_id in self._server_prompts:
            self._server_prompts[prompt.server_id].discard(name)
        return True

    async def get_prompt(self, name: str) -> MCPPrompt | None:
        """Get a prompt by its name.

        Args:
            name: The prompt name.

        Returns:
            The MCPPrompt if found, None otherwise.
        """
        return self._prompts.get(name)

    async def list_prompts(self, server_id: str | None = None) -> list[MCPPrompt]:
        """List all prompts, optionally filtered by server.

        Args:
            server_id: Optional server to filter by.

        Returns:
            A list of MCPPrompt instances.
        """
        if server_id is not None:
            names = self._server_prompts.get(server_id, set())
            return [self._prompts[name] for name in names if name in self._prompts]
        return list(self._prompts.values())

    async def render_prompt(self, name: str, arguments: dict[str, Any] | None = None) -> str | None:
        """Render a prompt template with the given arguments.

        Substitutes {arg_name} placeholders in the template with
        the provided argument values.

        Args:
            name: The prompt name to render.
            arguments: Arguments to substitute into the template.

        Returns:
            The rendered prompt string, or None if not found.
        """
        prompt = self._prompts.get(name)
        if prompt is None:
            return None

        template = prompt.template
        if arguments:
            for key, value in arguments.items():
                template = template.replace(f"{{{key}}}", str(value))

        return template

    async def remove_server_prompts(self, server_id: str) -> int:
        """Remove all prompts for a server.

        Args:
            server_id: The server whose prompts to remove.

        Returns:
            Number of prompts removed.
        """
        names = self._server_prompts.pop(server_id, set())
        for name in names:
            self._prompts.pop(name, None)
        return len(names)

    @property
    def prompt_count(self) -> int:
        """Return total number of registered prompts."""
        return len(self._prompts)
