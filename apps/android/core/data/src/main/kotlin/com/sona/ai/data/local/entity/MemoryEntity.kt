package com.sona.ai.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.sona.ai.data.local.converters.StringListConverter

/**
 * Room entity for storing memories in the local database.
 * Caches memories from the server for offline access.
 */
@Entity(tableName = "memories")
@TypeConverters(StringListConverter::class)
data class MemoryEntity(
    @PrimaryKey
    val id: String,
    val content: String,
    val category: String,
    val timestamp: Long,
    val source: String = "",
    val tags: List<String> = emptyList(),
    val importance: Float = 0.5f,
    val isSynced: Boolean = true,
    val lastUpdated: Long = System.currentTimeMillis()
)
