package com.sona.ai.domain.repository

import com.sona.ai.domain.model.Memory
import com.sona.ai.domain.model.MemoryType
import kotlinx.coroutines.flow.Flow

/**
 * Repository interface for memory operations.
 */
interface MemoryRepository {

    /**
     * Gets all memories for the current user.
     */
    fun getMemories(): Flow<List<Memory>>

    /**
     * Gets memories filtered by type.
     */
    fun getMemoriesByType(type: MemoryType): Flow<List<Memory>>

    /**
     * Searches memories by content.
     */
    suspend fun searchMemories(query: String): List<Memory>

    /**
     * Creates a new memory entry.
     */
    suspend fun createMemory(content: String, type: MemoryType, importance: Float): Memory

    /**
     * Deletes a memory by ID.
     */
    suspend fun deleteMemory(memoryId: String)
}
