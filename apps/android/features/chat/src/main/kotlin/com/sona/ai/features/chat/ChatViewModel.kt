package com.sona.ai.features.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.domain.model.ChatMessage
import com.sona.ai.domain.model.MessageRole
import com.sona.ai.domain.repository.ChatRepository
import com.sona.ai.domain.usecase.SendMessageUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

/**
 * ViewModel for the Chat screen.
 * Manages message state, sending messages, and streaming responses.
 */
@HiltViewModel
class ChatViewModel @Inject constructor(
    private val sendMessageUseCase: SendMessageUseCase,
    private val chatRepository: ChatRepository
) : ViewModel() {

    private val _state = MutableStateFlow<ChatState>(ChatState.Loading)
    val state: StateFlow<ChatState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<ChatEvent>()
    val events: SharedFlow<ChatEvent> = _events.asSharedFlow()

    private var currentConversationId: String = ""

    init {
        initializeConversation()
    }

    private fun initializeConversation() {
        viewModelScope.launch {
            try {
                val conversation = chatRepository.createConversation("New Chat")
                currentConversationId = conversation.id

                // Observe messages for this conversation
                chatRepository.getMessages(currentConversationId)
                    .onEach { messages ->
                        _state.update { currentState ->
                            when (currentState) {
                                is ChatState.Success -> currentState.copy(
                                    messages = messages,
                                    conversationId = currentConversationId
                                )
                                else -> ChatState.Success(
                                    messages = messages,
                                    conversationId = currentConversationId
                                )
                            }
                        }
                    }
                    .catch { e ->
                        _state.value = ChatState.Error(
                            message = e.message ?: "Failed to load messages"
                        )
                    }
                    .launchIn(viewModelScope)

                _state.value = ChatState.Success(conversationId = currentConversationId)
            } catch (e: Exception) {
                _state.value = ChatState.Error(message = e.message ?: "Failed to start conversation")
            }
        }
    }

    /**
     * Sends a user message and gets the AI response.
     */
    fun sendMessage(content: String) {
        if (content.isBlank()) return

        viewModelScope.launch {
            try {
                // Add user message to UI immediately
                val userMessage = ChatMessage(
                    id = UUID.randomUUID().toString(),
                    role = MessageRole.USER,
                    content = content,
                    timestamp = System.currentTimeMillis(),
                    conversationId = currentConversationId
                )

                updateMessages { it + userMessage }
                _events.emit(ChatEvent.ScrollToBottom)

                // Start streaming
                setStreaming(true)

                val response = sendMessageUseCase.execute(currentConversationId, content)
                updateMessages { it + response }

                setStreaming(false)
                _events.emit(ChatEvent.ScrollToBottom)
                _events.emit(ChatEvent.MessageSent)
            } catch (e: Exception) {
                setStreaming(false)
                _events.emit(ChatEvent.ShowError(e.message ?: "Failed to send message"))
            }
        }
    }

    /**
     * Sends a message with streaming response.
     */
    fun sendMessageStreaming(content: String) {
        if (content.isBlank()) return

        viewModelScope.launch {
            val userMessage = ChatMessage(
                id = UUID.randomUUID().toString(),
                role = MessageRole.USER,
                content = content,
                timestamp = System.currentTimeMillis(),
                conversationId = currentConversationId
            )
            updateMessages { it + userMessage }
            _events.emit(ChatEvent.ScrollToBottom)

            setStreaming(true)
            var streamedContent = ""

            sendMessageUseCase.executeStreaming(currentConversationId, content)
                .onEach { token ->
                    streamedContent += token
                    _state.update { currentState ->
                        if (currentState is ChatState.Success) {
                            currentState.copy(streamingContent = streamedContent)
                        } else currentState
                    }
                }
                .catch { e ->
                    setStreaming(false)
                    _events.emit(ChatEvent.ShowError(e.message ?: "Streaming failed"))
                }
                .collect {
                    // Final collection complete
                }

            // Finalize streaming message
            if (streamedContent.isNotEmpty()) {
                val assistantMessage = ChatMessage(
                    id = UUID.randomUUID().toString(),
                    role = MessageRole.ASSISTANT,
                    content = streamedContent,
                    timestamp = System.currentTimeMillis(),
                    conversationId = currentConversationId
                )
                chatRepository.saveMessage(assistantMessage)
                updateMessages { it + assistantMessage }
            }

            setStreaming(false)
            _state.update { if (it is ChatState.Success) it.copy(streamingContent = "") else it }
            _events.emit(ChatEvent.ScrollToBottom)
        }
    }

    /**
     * Loads an existing conversation by ID.
     */
    fun loadConversation(conversationId: String) {
        currentConversationId = conversationId
        chatRepository.getMessages(conversationId)
            .onEach { messages ->
                _state.value = ChatState.Success(
                    messages = messages,
                    conversationId = conversationId
                )
            }
            .launchIn(viewModelScope)
    }

    private fun setStreaming(streaming: Boolean) {
        _state.update { currentState ->
            if (currentState is ChatState.Success) {
                currentState.copy(isStreaming = streaming)
            } else currentState
        }
    }

    private fun updateMessages(transform: (List<ChatMessage>) -> List<ChatMessage>) {
        _state.update { currentState ->
            if (currentState is ChatState.Success) {
                currentState.copy(messages = transform(currentState.messages))
            } else currentState
        }
    }
}
