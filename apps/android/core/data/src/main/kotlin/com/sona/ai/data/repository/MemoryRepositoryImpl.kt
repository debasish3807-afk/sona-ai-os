package com.sona.ai.data.repository

import com.sona.ai.data.mapper.MessageMapper.toDomain
import com.sona.ai.data.mapper.MessageMapper.toDto
import com.sona.ai.data.remote.SonaApi
import com.sona.ai.data.remote.dto.MemoryDto
import com.sona.ai.domain.model.Memory
import com.sona.ai.domain.model.MemoryType
import com.sona.ai.domain.repository.MemoryRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Implementation of [MemoryRepository] using the Sona API.
 */
@Singleton
class MemoryRepositoryImpl @Inject constructor(
    private val api: SonaApi
) : MemoryRepository {

    override fun getMemories(): Flow<List<Memory>> = flow {
        val memories = api.getMemories().map { it.toDomain() }
        emit(memories)
    }

    override fun getMemoriesByType(type: MemoryType): Flow<List<Memory>> = flow {
        val memories = api.getMemories()
            .map { it.toDomain() }
            .filter { it.type == type }
        emit(memories)
    }

    override suspend fun searchMemories(query: String): List<Memory> {
        return api.searchMemories(query).map { it.toDomain() }
    }

    override suspend fun createMemory(
        content: String,
        type: MemoryType,
        importance: Float
    ): Memory {
        val dto = MemoryDto(
            content = content,
            type = type.name.lowercase(),
            importance = importance
        )
        return api.createMemory(dto).toDomain()
    }

    override suspend fun deleteMemory(memoryId: String) {
        api.deleteMemory(memoryId)
    }
}
