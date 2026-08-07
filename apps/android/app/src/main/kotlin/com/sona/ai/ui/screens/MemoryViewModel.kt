package com.sona.ai.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.domain.model.Memory
import com.sona.ai.domain.repository.MemoryRepository
import com.sona.ai.domain.usecase.GetMemoriesUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Memory screen.
 */
@HiltViewModel
class MemoryViewModel @Inject constructor(
    private val getMemoriesUseCase: GetMemoriesUseCase,
    private val memoryRepository: MemoryRepository
) : ViewModel() {

    private val _state = MutableStateFlow(MemoryState())
    val state: StateFlow<MemoryState> = _state.asStateFlow()

    init {
        loadMemories()
    }

    private fun loadMemories() {
        getMemoriesUseCase.execute()
            .onEach { memories ->
                _state.update {
                    it.copy(isLoading = false, memories = memories)
                }
            }
            .catch { e ->
                _state.update {
                    it.copy(isLoading = false, error = e.message)
                }
            }
            .launchIn(viewModelScope)
    }

    fun deleteMemory(memoryId: String) {
        viewModelScope.launch {
            try {
                memoryRepository.deleteMemory(memoryId)
                _state.update { current ->
                    current.copy(
                        memories = current.memories.filter { it.id != memoryId }
                    )
                }
            } catch (e: Exception) {
                _state.update { it.copy(error = e.message) }
            }
        }
    }
}

/**
 * UI state for the Memory screen.
 */
data class MemoryState(
    val isLoading: Boolean = true,
    val memories: List<Memory> = emptyList(),
    val error: String? = null
)
