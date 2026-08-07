package com.sona.ai.domain.model

/**
 * Represents a single chat message in a conversation.
 */
data class ChatMessage(
    val id: String,
    val role: MessageRole,
    val content: String,
    val timestamp: Long,
    val conversationId: String = "",
    val isStreaming: Boolean = false
)

/**
 * Role of the message sender.
 */
enum class MessageRole {
    USER,
    ASSISTANT,
    SYSTEM
}
