package com.sona.ai.data.mapper

import com.sona.ai.data.local.entity.ConversationEntity
import com.sona.ai.data.local.entity.MessageEntity
import com.sona.ai.data.remote.dto.ChatResponseDto
import com.sona.ai.data.remote.dto.MemoryDto
import com.sona.ai.domain.model.ChatMessage
import com.sona.ai.domain.model.Conversation
import com.sona.ai.domain.model.Memory
import com.sona.ai.domain.model.MemoryType
import com.sona.ai.domain.model.MessageRole

/**
 * Maps between domain models, entities, and DTOs.
 */
object MessageMapper {

    // ─── Message Mapping ────────────────────────────────────────────────

    fun MessageEntity.toDomain(): ChatMessage = ChatMessage(
        id = id,
        role = MessageRole.valueOf(role.uppercase()),
        content = content,
        timestamp = timestamp,
        conversationId = conversationId
    )

    fun ChatMessage.toEntity(): MessageEntity = MessageEntity(
        id = id,
        conversationId = conversationId,
        role = role.name,
        content = content,
        timestamp = timestamp
    )

    fun ChatResponseDto.toDomain(): ChatMessage = ChatMessage(
        id = id,
        role = MessageRole.ASSISTANT,
        content = content,
        timestamp = createdAt,
        conversationId = conversationId
    )

    // ─── Conversation Mapping ───────────────────────────────────────────

    fun ConversationEntity.toDomain(messages: List<ChatMessage> = emptyList()): Conversation =
        Conversation(
            id = id,
            title = title,
            messages = messages,
            createdAt = createdAt,
            updatedAt = updatedAt
        )

    fun Conversation.toEntity(): ConversationEntity = ConversationEntity(
        id = id,
        title = title,
        createdAt = createdAt,
        updatedAt = updatedAt
    )

    // ─── Memory Mapping ─────────────────────────────────────────────────

    fun MemoryDto.toDomain(): Memory = Memory(
        id = id,
        content = content,
        type = try {
            MemoryType.valueOf(type.uppercase())
        } catch (_: Exception) {
            MemoryType.SEMANTIC
        },
        importance = importance,
        createdAt = createdAt
    )

    fun Memory.toDto(): MemoryDto = MemoryDto(
        id = id,
        content = content,
        type = type.name.lowercase(),
        importance = importance,
        createdAt = createdAt
    )
}
