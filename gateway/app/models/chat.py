"""Chat request/response models for the API Gateway.

Defines the contract for chat completions API endpoints with strict validation.
"""

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ChatRole(StrEnum):
    """Allowed chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: ChatRole
    content: str = Field(min_length=1, max_length=100000)

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Ensure role is one of the allowed values."""
        allowed = {"user", "assistant", "system"}
        if str(v).lower() not in allowed:
            raise ValueError(f"role must be one of {allowed}, got '{v}'")
        return str(v).lower()


class ChatRequest(BaseModel):
    """Incoming chat completion request."""

    messages: list[ChatMessage] = Field(min_length=1)
    model: str = "default"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    stream: bool = False
    user_id: str | None = None


class TokenUsage(BaseModel):
    """Token usage statistics for a response."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class ChatResponse(BaseModel):
    """Chat completion response."""

    id: UUID = Field(default_factory=uuid4)
    messages: list[ChatMessage]
    model: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finish_reason: str = "stop"
