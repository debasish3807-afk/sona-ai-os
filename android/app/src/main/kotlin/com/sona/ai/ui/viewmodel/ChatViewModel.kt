package com.sona.ai.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.data.repository.SonaRepository
import com.sona.ai.domain.model.ChatMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val repository: SonaRepository
) : ViewModel() {

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading

    fun send(content: String) {
        if (content.isBlank()) return

        val userMsg = ChatMessage(role = "user", content = content)
        _messages.value = _messages.value + userMsg
        _isLoading.value = true

        viewModelScope.launch {
            val result = repository.sendMessage(_messages.value)
            result.onSuccess { response ->
                val aiMsg = ChatMessage(role = "assistant", content = response.content)
                _messages.value = _messages.value + aiMsg
            }.onFailure { error ->
                val errMsg = ChatMessage(role = "assistant", content = "[Error: ${error.message}]")
                _messages.value = _messages.value + errMsg
            }
            _isLoading.value = false
        }
    }
}
