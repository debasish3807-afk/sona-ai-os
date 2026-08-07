package com.sona.ai.domain.model

/**
 * Represents a memory entry stored by the AI system.
 */
data class Memory(
    val id: String,
    val content: String,
    val type: MemoryType,
    val importance: Float,
    val createdAt: Long
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
