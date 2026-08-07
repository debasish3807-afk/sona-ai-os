package com.sona.ai.features.voice.assistant

import com.sona.ai.features.voice.recognition.SpeechRecognitionManager
import com.sona.ai.features.voice.tts.TtsManager
import com.sona.ai.features.voice.commands.VoiceCommandRouter
import com.sona.ai.features.voice.context.ConversationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Possible modes for the voice assistant.
 */
enum class AssistantMode {
    IDLE,
    LISTENING,
    PROCESSING,
    SPEAKING,
    CONTINUOUS
}

/**
 * Core voice assistant orchestrator.
 * Manages the lifecycle of voice interactions including listening, processing,
 * and speaking responses. Coordinates between speech recognition, TTS, and
 * command routing.
 */
@Singleton
class VoiceAssistant @Inject constructor(
    private val speechManager: SpeechRecognitionManager,
    private val ttsManager: TtsManager,
    private val commandRouter: VoiceCommandRouter,
    private val conversationContext: ConversationContext
) {

    private val _mode = MutableStateFlow(AssistantMode.IDLE)
    val mode: StateFlow<AssistantMode> = _mode.asStateFlow()

    /**
     * Starts listening for user speech input.
     */
    suspend fun startListening() {
        _mode.value = AssistantMode.LISTENING
        speechManager.startListening()
    }

    /**
     * Stops listening for speech input.
     */
    suspend fun stopListening() {
        speechManager.stopListening()
        _mode.value = AssistantMode.IDLE
    }

    /**
     * Processes user input text through the command router and returns a response.
     */
    suspend fun processInput(text: String): String {
        _mode.value = AssistantMode.PROCESSING
        val context = conversationContext.getContext()
        val response = commandRouter.route(text, context)
        conversationContext.addTurn(text, response)
        return response
    }

    /**
     * Speaks the given text using TTS.
     */
    suspend fun speak(text: String) {
        _mode.value = AssistantMode.SPEAKING
        ttsManager.speak(text)
        _mode.value = AssistantMode.IDLE
    }

    /**
     * Enables continuous listening mode where the assistant
     * continuously listens for commands after each response.
     */
    fun startContinuousMode() {
        _mode.value = AssistantMode.CONTINUOUS
    }

    /**
     * Disables continuous listening mode.
     */
    fun stopContinuousMode() {
        _mode.value = AssistantMode.IDLE
    }
}
