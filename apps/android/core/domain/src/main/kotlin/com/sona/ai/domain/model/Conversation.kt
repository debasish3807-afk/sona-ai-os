package com.sona.ai.domain.model

/**
 * Represents a conversation containing multiple messages.
 */
data class Conversation(
    val id: String,
    val title: String,
    val messages: List<ChatMessage> = emptyList(),
    val createdAt: Long,
    val updatedAt: Long = createdAt
)
