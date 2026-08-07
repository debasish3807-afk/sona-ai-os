package com.sona.ai.domain.repository

import com.sona.ai.domain.model.ChatMessage
import com.sona.ai.domain.model.Conversation
import kotlinx.coroutines.flow.Flow

/**
 * Repository interface for chat operations.
 */
interface ChatRepository {

    /**
     * Sends a message and returns the AI response.
     */
    suspend fun sendMessage(conversationId: String, content: String): ChatMessage

    /**
     * Sends a message and streams the AI response token-by-token.
     */
    fun streamMessage(conversationId: String, content: String): Flow<String>

    /**
     * Gets all conversations for the current user.
     */
    fun getConversations(): Flow<List<Conversation>>

    /**
     * Gets messages for a specific conversation.
     */
    fun getMessages(conversationId: String): Flow<List<ChatMessage>>

    /**
     * Creates a new conversation.
     */
    suspend fun createConversation(title: String): Conversation

    /**
     * Deletes a conversation by ID.
     */
    suspend fun deleteConversation(conversationId: String)

    /**
     * Saves a message to local storage.
     */
    suspend fun saveMessage(message: ChatMessage)
}
