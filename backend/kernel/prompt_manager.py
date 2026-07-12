"""Prompt lifecycle management.

Manages the creation, templating, validation, and optimization
of prompts sent to language models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class PromptRole(str, Enum):
    """Role assignments within a prompt."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class PromptFormat(str, Enum):
    """Supported prompt output formats."""

    CHAT = "chat"
    COMPLETION = "completion"
    INSTRUCTION = "instruction"


@dataclass
class PromptMessage:
    """A single message within a prompt.

    Attributes:
        role: The message role.
        content: The message content.
        name: Optional name for the message sender.
        metadata: Additional message metadata.
    """

    role: PromptRole
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """A reusable prompt template with variable substitution.

    Attributes:
        template_id: Unique template identifier.
        name: Human-readable template name.
        description: Template description and usage notes.
        template: The template string with {{variable}} placeholders.
        variables: Expected variables and their descriptions.
        default_role: Default role for the rendered prompt.
        format: Output format for this template.
        version: Template version for tracking changes.
        metadata: Additional template metadata.
    """

    name: str
    template: str
    template_id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    variables: Dict[str, str] = field(default_factory=dict)
    default_role: PromptRole = PromptRole.SYSTEM
    format: PromptFormat = PromptFormat.CHAT
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderedPrompt:
    """A fully rendered prompt ready for model consumption.

    Attributes:
        prompt_id: Unique identifier for this rendered prompt.
        messages: Ordered list of prompt messages.
        template_id: Source template identifier (if applicable).
        variables_used: Variables that were substituted.
        token_estimate: Estimated token count.
        format: The prompt format.
        created_at: Rendering timestamp.
        metadata: Additional prompt metadata.
    """

    messages: List[PromptMessage]
    prompt_id: str = field(default_factory=lambda: str(uuid4()))
    template_id: Optional[str] = None
    variables_used: Dict[str, Any] = field(default_factory=dict)
    token_estimate: int = 0
    format: PromptFormat = PromptFormat.CHAT
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromptManager(ABC):
    """Abstract interface for prompt lifecycle management.

    Handles template registration, variable rendering, validation,
    and optimization of prompts before they are sent to models.
    """

    @abstractmethod
    async def register_template(self, template: PromptTemplate) -> str:
        """Register a new prompt template.

        Args:
            template: The template to register.

        Returns:
            The template_id of the registered template.

        Raises:
            ValueError: If a template with the same ID exists.
        """
        ...

    @abstractmethod
    async def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Retrieve a template by ID.

        Args:
            template_id: The template identifier.

        Returns:
            PromptTemplate or None if not found.
        """
        ...

    @abstractmethod
    async def list_templates(
        self,
        format: Optional[PromptFormat] = None,
    ) -> List[PromptTemplate]:
        """List available templates with optional filtering.

        Args:
            format: Optional filter by prompt format.

        Returns:
            List of matching templates.
        """
        ...

    @abstractmethod
    async def render(
        self,
        template_id: str,
        variables: Dict[str, Any],
    ) -> RenderedPrompt:
        """Render a template with provided variables.

        Substitutes variables into the template and produces
        a fully rendered prompt ready for model consumption.

        Args:
            template_id: The template to render.
            variables: Variable values for substitution.

        Returns:
            Fully rendered RenderedPrompt.

        Raises:
            ValueError: If template not found or variables invalid.
        """
        ...

    @abstractmethod
    async def compose(
        self,
        messages: List[PromptMessage],
        system_prompt: Optional[str] = None,
    ) -> RenderedPrompt:
        """Compose a prompt from individual messages.

        Creates a rendered prompt directly from messages without
        using a template.

        Args:
            messages: The messages to compose into a prompt.
            system_prompt: Optional system instruction to prepend.

        Returns:
            Composed RenderedPrompt.
        """
        ...

    @abstractmethod
    async def validate(self, prompt: RenderedPrompt) -> List[str]:
        """Validate a rendered prompt for correctness.

        Checks for common issues such as empty messages,
        invalid role sequences, and token budget violations.

        Args:
            prompt: The prompt to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        ...

    @abstractmethod
    async def optimize(
        self,
        prompt: RenderedPrompt,
        max_tokens: int,
    ) -> RenderedPrompt:
        """Optimize a prompt to fit within a token budget.

        Applies compression and truncation strategies to reduce
        prompt size while preserving critical information.

        Args:
            prompt: The prompt to optimize.
            max_tokens: Maximum allowed token count.

        Returns:
            Optimized RenderedPrompt within the token budget.
        """
        ...
