package com.sona.ai.domain.usecase

import com.sona.ai.domain.model.Memory
import com.sona.ai.domain.model.MemoryType
import com.sona.ai.domain.repository.MemoryRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

/**
 * Use case for retrieving memories.
 */
class GetMemoriesUseCase @Inject constructor(
    private val memoryRepository: MemoryRepository
) {

    /**
     * Gets all memories.
     */
    fun execute(): Flow<List<Memory>> {
        return memoryRepository.getMemories()
    }

    /**
     * Gets memories filtered by type.
     */
    fun executeByType(type: MemoryType): Flow<List<Memory>> {
        return memoryRepository.getMemoriesByType(type)
    }

    /**
     * Searches memories by query string.
     */
    suspend fun search(query: String): List<Memory> {
        require(query.isNotBlank()) { "Search query cannot be blank" }
        return memoryRepository.searchMemories(query)
    }
}
