package com.sona.ai.features.memory

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.domain.model.MemoryType
import com.sona.ai.domain.repository.MemoryRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the memory browser screen.
 * Manages memory listing, searching, and deletion.
 */
@HiltViewModel
class MemoryViewModel @Inject constructor(
    private val memoryRepository: MemoryRepository
) : ViewModel() {

    private val _state = MutableStateFlow<MemoryState>(MemoryState.Loading)
    val state: StateFlow<MemoryState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<MemoryEvent>()
    val events: SharedFlow<MemoryEvent> = _events.asSharedFlow()

    private var searchJob: Job? = null

    init {
        loadMemories()
    }

    /**
     * Loads all memories from the repository.
     */
    private fun loadMemories() {
        viewModelScope.launch {
            try {
                val memories = memoryRepository.getMemories().first()
                _state.value = MemoryState.Success(
                    memories = memories.map { it.toMemoryItem() }
                )
            } catch (e: Exception) {
                _state.value = MemoryState.Error(e.message ?: "Failed to load memories")
            }
        }
    }

    /**
     * Updates the search query with debounce.
     */
    fun onSearchQueryChanged(query: String) {
        _state.update { current ->
            if (current is MemoryState.Success) {
                current.copy(searchQuery = query, isSearching = true)
            } else current
        }

        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(300) // Debounce
            performSearch(query)
        }
    }

    /**
     * Performs a search against the memory repository.
     */
    private suspend fun performSearch(query: String) {
        val currentState = _state.value as? MemoryState.Success ?: return

        try {
            if (query.isBlank()) {
                loadMemories()
            } else {
                val results = memoryRepository.searchMemories(query)
                _state.value = currentState.copy(
                    memories = results.map { it.toMemoryItem() },
                    isSearching = false
                )
            }
        } catch (e: Exception) {
            _state.update { current ->
                if (current is MemoryState.Success) {
                    current.copy(isSearching = false)
                } else current
            }
            _events.emit(MemoryEvent.ShowError(e.message ?: "Search failed"))
        }
    }

    /**
     * Applies a category filter.
     */
    fun onFilterChanged(filter: MemoryFilter) {
        _state.update { current ->
            if (current is MemoryState.Success) {
                current.copy(filter = filter)
            } else current
        }
        // Reload with filter
        viewModelScope.launch {
            try {
                val memories = if (filter == MemoryFilter.ALL) {
                    memoryRepository.getMemories().first()
                } else {
                    val memoryType = filter.toMemoryType()
                    memoryRepository.getMemoriesByType(memoryType).first()
                }
                _state.update { current ->
                    if (current is MemoryState.Success) {
                        current.copy(memories = memories.map { it.toMemoryItem() })
                    } else current
                }
            } catch (e: Exception) {
                _events.emit(MemoryEvent.ShowError(e.message ?: "Filter failed"))
            }
        }
    }

    /**
     * Deletes a memory by ID.
     */
    fun deleteMemory(id: String) {
        viewModelScope.launch {
            try {
                memoryRepository.deleteMemory(id)
                _state.update { current ->
                    if (current is MemoryState.Success) {
                        current.copy(memories = current.memories.filter { it.id != id })
                    } else current
                }
                _events.emit(MemoryEvent.MemoryDeleted(id))
            } catch (e: Exception) {
                _events.emit(MemoryEvent.ShowError(e.message ?: "Delete failed"))
            }
        }
    }

    /**
     * Refreshes the memory list.
     */
    fun refresh() {
        _state.value = MemoryState.Loading
        loadMemories()
    }

    private fun MemoryFilter.toMemoryType(): MemoryType = when (this) {
        MemoryFilter.ALL -> MemoryType.SEMANTIC
        MemoryFilter.CONVERSATIONS -> MemoryType.EPISODIC
        MemoryFilter.PREFERENCES -> MemoryType.PREFERENCE
        MemoryFilter.FACTS -> MemoryType.SEMANTIC
        MemoryFilter.TASKS -> MemoryType.PROCEDURAL
    }

    private fun com.sona.ai.domain.model.Memory.toMemoryItem() = MemoryItem(
        id = id,
        content = content,
        category = category,
        timestamp = timestamp,
        source = source,
        tags = tags,
        importance = importance
    )
}
