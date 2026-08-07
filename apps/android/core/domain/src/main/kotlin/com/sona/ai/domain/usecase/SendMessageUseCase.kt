package com.sona.ai.domain.usecase

import com.sona.ai.domain.model.ChatMessage
import com.sona.ai.domain.model.MessageRole
import com.sona.ai.domain.repository.ChatRepository
import kotlinx.coroutines.flow.Flow
import java.util.UUID
import javax.inject.Inject

/**
 * Use case for sending a chat message and receiving a response.
 * Handles both streaming and non-streaming modes.
 */
class SendMessageUseCase @Inject constructor(
    private val chatRepository: ChatRepository
) {

    /**
     * Sends a message and returns the complete AI response.
     */
    suspend fun execute(conversationId: String, content: String): ChatMessage {
        // Save user message first
        val userMessage = ChatMessage(
            id = UUID.randomUUID().toString(),
            role = MessageRole.USER,
            content = content,
            timestamp = System.currentTimeMillis(),
            conversationId = conversationId
        )
        chatRepository.saveMessage(userMessage)

        // Send to API and get response
        return chatRepository.sendMessage(conversationId, content)
    }

    /**
     * Sends a message and streams the AI response token-by-token.
     */
    fun executeStreaming(conversationId: String, content: String): Flow<String> {
        return chatRepository.streamMessage(conversationId, content)
    }
}
