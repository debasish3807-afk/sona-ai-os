package com.sona.ai.features.memory

/**
 * UI state for the memory browser screen.
 */
sealed interface MemoryState {

    /** Loading memories. */
    data object Loading : MemoryState

    /** Memories loaded successfully. */
    data class Success(
        val memories: List<MemoryItem> = emptyList(),
        val searchQuery: String = "",
        val filter: MemoryFilter = MemoryFilter.ALL,
        val isSearching: Boolean = false
    ) : MemoryState

    /** Error loading memories. */
    data class Error(
        val message: String
    ) : MemoryState
}

/**
 * Represents a single memory item.
 */
data class MemoryItem(
    val id: String,
    val content: String,
    val category: String,
    val timestamp: Long,
    val source: String = "",
    val tags: List<String> = emptyList(),
    val importance: Float = 0.5f
)

/**
 * Filters for memory browsing.
 */
enum class MemoryFilter(val label: String) {
    ALL("All"),
    CONVERSATIONS("Conversations"),
    PREFERENCES("Preferences"),
    FACTS("Facts"),
    TASKS("Tasks")
}

/**
 * One-time UI events for the memory screen.
 */
sealed interface MemoryEvent {
    data class ShowError(val message: String) : MemoryEvent
    data class MemoryDeleted(val id: String) : MemoryEvent
}
