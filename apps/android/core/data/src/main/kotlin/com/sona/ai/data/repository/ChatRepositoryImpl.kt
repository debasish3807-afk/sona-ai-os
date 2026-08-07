package com.sona.ai.data.repository

import com.sona.ai.data.local.dao.ConversationDao
import com.sona.ai.data.local.dao.MessageDao
import com.sona.ai.data.local.entity.ConversationEntity
import com.sona.ai.data.mapper.MessageMapper.toDomain
import com.sona.ai.data.mapper.MessageMapper.toEntity
import com.sona.ai.data.remote.SonaApi
import com.sona.ai.data.remote.SseClient
import com.sona.ai.data.remote.dto.ChatRequestDto
import com.sona.ai.domain.model.ChatMessage
import com.sona.ai.domain.model.Conversation
import com.sona.ai.domain.repository.ChatRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Implementation of [ChatRepository] using Retrofit (remote) and Room (local).
 */
@Singleton
class ChatRepositoryImpl @Inject constructor(
    private val api: SonaApi,
    private val sseClient: SseClient,
    private val messageDao: MessageDao,
    private val conversationDao: ConversationDao
) : ChatRepository {

    override suspend fun sendMessage(conversationId: String, content: String): ChatMessage {
        val request = ChatRequestDto(
            conversationId = conversationId,
            message = content,
            stream = false
        )
        val response = api.sendMessage(request)
        val message = response.toDomain()

        // Cache response locally
        messageDao.insertMessage(message.toEntity())
        conversationDao.updateTimestamp(conversationId, System.currentTimeMillis())

        return message
    }

    override fun streamMessage(conversationId: String, content: String): Flow<String> {
        val body = """
            {
                "conversation_id": "$conversationId",
                "message": "$content",
                "stream": true
            }
        """.trimIndent()

        return sseClient.stream(
            url = "api/v1/chat/completions/stream",
            body = body,
            token = "" // Token handled by interceptor
        )
    }

    override fun getConversations(): Flow<List<Conversation>> {
        return conversationDao.getAllConversations().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override fun getMessages(conversationId: String): Flow<List<ChatMessage>> {
        return messageDao.getMessagesByConversation(conversationId).map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun createConversation(title: String): Conversation {
        val conversation = Conversation(
            id = UUID.randomUUID().toString(),
            title = title,
            createdAt = System.currentTimeMillis()
        )
        conversationDao.insertConversation(conversation.toEntity())
        return conversation
    }

    override suspend fun deleteConversation(conversationId: String) {
        messageDao.deleteMessagesByConversation(conversationId)
        conversationDao.deleteConversation(conversationId)
    }

    override suspend fun saveMessage(message: ChatMessage) {
        messageDao.insertMessage(message.toEntity())
        conversationDao.updateTimestamp(message.conversationId, System.currentTimeMillis())
    }
}
