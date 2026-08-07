package com.sona.ai.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.sona.ai.data.local.dao.ConversationDao
import com.sona.ai.data.local.dao.MessageDao
import com.sona.ai.data.local.entity.ConversationEntity
import com.sona.ai.data.local.entity.MessageEntity

/**
 * Room database for the Sona AI app.
 */
@Database(
    entities = [
        MessageEntity::class,
        ConversationEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class SonaDatabase : RoomDatabase() {

    abstract fun messageDao(): MessageDao

    abstract fun conversationDao(): ConversationDao

    companion object {
        const val DATABASE_NAME = "sona_ai_database"
    }
}
