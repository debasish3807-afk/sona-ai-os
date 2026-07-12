"""Conversation memory - chat history management.

This module defines the conversation memory interface for managing
chat history, dialogue context, and conversational state. It handles
message storage, conversation lifecycle, summarization of long
conversations, and archival.

Classes:
    ConversationConfig: Configuration for conversation memory behavior.
    ConversationMessage: A single message in a conversation.
    Conversation: A complete conversation with messages and metadata.
    ConversationMemory: Abstract interface extending MemoryStore for conversation memory.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .base import MemoryStore


@dataclass(frozen=True, slots=True)
class ConversationConfig:
    """Configuration for conversation memory behavior.

    Controls capacity, summarization triggers, and archival policies
    for conversation management.

    Attributes:
        max_messages: Maximum messages per conversation before summarization.
        max_conversations: Maximum number of active conversations.
        summarize_after: Number of messages after which to generate a summary.
        archive_after_hours: Hours of inactivity before auto-archival.
        max_token_per_message: Maximum tokens per individual message.
        retain_summaries: Whether to keep summaries when archiving.
    """

    max_messages: int = 1000
    max_conversations: int = 500
    summarize_after: int = 50
    archive_after_hours: int = 72
    max_token_per_message: int = 4096
    retain_summaries: bool = True


@dataclass(slots=True)
class ConversationMessage:
    """A single message in a conversation.

    Represents one turn in a dialogue with role, content, and metadata.

    Attributes:
        message_id: Unique identifier for this message (UUID4).
        conversation_id: ID of the conversation this message belongs to.
        role: The role of the message sender ('user', 'assistant', 'system', 'tool').
        content: The text content of the message.
        timestamp: UTC timestamp when this message was sent.
        token_count: Estimated token count of the message content.
        name: Optional name identifier for the sender.
        tool_call_id: Optional tool call ID for tool response messages.
        metadata: Additional message metadata.
    """

    conversation_id: str
    role: str
    content: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    token_count: int = 0
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Conversation:
    """A complete conversation with messages and metadata.

    Represents a dialogue thread including all messages, participants,
    and lifecycle state.

    Attributes:
        conversation_id: Unique identifier for this conversation (UUID4).
        user_id: ID of the user who owns this conversation.
        title: Optional title or subject of the conversation.
        messages: List of messages in chronological order.
        created_at: UTC timestamp when this conversation was created.
        updated_at: UTC timestamp of the most recent activity.
        summary: Optional generated summary of the conversation.
        archived: Whether this conversation has been archived.
        message_count: Total number of messages in the conversation.
        total_tokens: Total token count across all messages.
        metadata: Additional conversation metadata.
    """

    user_id: str
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    messages: list[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    summary: Optional[str] = None
    archived: bool = False
    message_count: int = 0
    total_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversationMemory(MemoryStore):
    """Abstract interface for conversation memory operations.

    Extends the base MemoryStore with conversation lifecycle management,
    message operations, summarization, and archival.
    """

    @abstractmethod
    async def create_conversation(self, user_id: str, title: Optional[str] = None) -> str:
        """Create a new conversation.

        Args:
            user_id: The user ID who owns this conversation.
            title: Optional title for the conversation.

        Returns:
            The conversation_id of the created conversation.
        """
        ...

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation by its ID.

        Args:
            conversation_id: The unique identifier of the conversation.

        Returns:
            The conversation if found, None otherwise.
        """
        ...

    @abstractmethod
    async def add_message(
        self, conversation_id: str, message: ConversationMessage
    ) -> None:
        """Add a message to an existing conversation.

        Updates the conversation's updated_at timestamp and message count.

        Args:
            conversation_id: The conversation to add the message to.
            message: The message to add.

        Raises:
            MemoryNotFoundError: If the conversation doesn't exist.
        """
        ...

    @abstractmethod
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before: Optional[datetime] = None,
    ) -> list[ConversationMessage]:
        """Get messages from a conversation with pagination.

        Args:
            conversation_id: The conversation to get messages from.
            limit: Maximum number of messages to return.
            before: Optional cursor - only return messages before this timestamp.

        Returns:
            List of messages in chronological order.
        """
        ...

    @abstractmethod
    async def summarize_conversation(self, conversation_id: str) -> str:
        """Generate or update the summary of a conversation.

        Creates a concise summary of the conversation's content
        for efficient context retrieval.

        Args:
            conversation_id: The conversation to summarize.

        Returns:
            The generated summary text.
        """
        ...

    @abstractmethod
    async def list_conversations(
        self, user_id: str, limit: int = 50, include_archived: bool = False
    ) -> list[Conversation]:
        """List conversations for a user.

        Args:
            user_id: The user whose conversations to list.
            limit: Maximum number of conversations to return.
            include_archived: Whether to include archived conversations.

        Returns:
            List of conversations ordered by most recently updated.
        """
        ...

    @abstractmethod
    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation.

        Marks the conversation as archived. Archived conversations are
        excluded from default listings but remain searchable.

        Args:
            conversation_id: The conversation to archive.

        Returns:
            True if the conversation was found and archived, False otherwise.
        """
        ...
