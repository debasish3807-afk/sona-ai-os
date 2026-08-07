package com.sona.ai.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.sona.ai.data.local.entity.ConversationEntity
import kotlinx.coroutines.flow.Flow

/**
 * Room DAO for conversation operations.
 */
@Dao
interface ConversationDao {

    @Query("SELECT * FROM conversations ORDER BY updated_at DESC")
    fun getAllConversations(): Flow<List<ConversationEntity>>

    @Query("SELECT * FROM conversations WHERE id = :conversationId")
    suspend fun getConversationById(conversationId: String): ConversationEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertConversation(conversation: ConversationEntity)

    @Query("UPDATE conversations SET updated_at = :updatedAt WHERE id = :conversationId")
    suspend fun updateTimestamp(conversationId: String, updatedAt: Long)

    @Query("DELETE FROM conversations WHERE id = :conversationId")
    suspend fun deleteConversation(conversationId: String)

    @Query("SELECT COUNT(*) FROM conversations")
    suspend fun getConversationCount(): Int
}
