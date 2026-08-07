package com.sona.ai.features.voice

/**
 * UI state for the voice chat screen.
 */
sealed interface VoiceState {

    /** Ready to start listening. */
    data object Idle : VoiceState

    /** Actively listening to user speech. */
    data class Listening(
        val amplitude: Float = 0f
    ) : VoiceState

    /** Processing speech-to-text and waiting for AI response. */
    data class Processing(
        val transcribedText: String = ""
    ) : VoiceState

    /** Speaking the AI response via TTS. */
    data class Speaking(
        val text: String,
        val progress: Float = 0f
    ) : VoiceState

    /** An error occurred. */
    data class Error(
        val message: String
    ) : VoiceState
}

/**
 * One-time UI events for the voice screen.
 */
sealed interface VoiceEvent {
    data class ShowError(val message: String) : VoiceEvent
    data object PermissionRequired : VoiceEvent
    data object VoiceSessionComplete : VoiceEvent
}
