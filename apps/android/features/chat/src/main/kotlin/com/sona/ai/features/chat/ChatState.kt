package com.sona.ai.features.chat

import com.sona.ai.domain.model.ChatMessage

/**
 * UI state for the chat screen.
 */
sealed interface ChatState {

    /** Initial loading state. */
    data object Loading : ChatState

    /** Chat is ready with messages. */
    data class Success(
        val messages: List<ChatMessage> = emptyList(),
        val conversationId: String = "",
        val isStreaming: Boolean = false,
        val streamingContent: String = ""
    ) : ChatState

    /** Error state with message. */
    data class Error(
        val message: String,
        val messages: List<ChatMessage> = emptyList()
    ) : ChatState
}

/**
 * One-time UI events for the chat screen.
 */
sealed interface ChatEvent {
    data object ScrollToBottom : ChatEvent
    data class ShowError(val message: String) : ChatEvent
    data object MessageSent : ChatEvent
}
