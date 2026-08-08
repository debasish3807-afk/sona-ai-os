package com.sona.ai.domain.model

/**
 * Represents a memory entry stored by the AI system.
 */
data class Memory(
    val id: String,
    val content: String,
    val type: MemoryType,
    val importance: Float,
    val createdAt: Long,
    val category: String = "",
    val timestamp: Long = 0L,
    val source: String = "",
    val tags: List<String> = emptyList()
)

/**
 * Classification of memory types.
 */
enum class MemoryType {
    EPISODIC,
    SEMANTIC,
    PROCEDURAL,
    PREFERENCE
}
