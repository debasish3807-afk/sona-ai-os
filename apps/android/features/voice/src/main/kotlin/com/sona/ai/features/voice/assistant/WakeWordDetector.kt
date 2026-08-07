package com.sona.ai.features.voice.assistant

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Detects wake words in speech input to activate the voice assistant.
 * Supports multiple wake word variants including "hey sona", "ok sona", and "sona".
 */
@Singleton
class WakeWordDetector @Inject constructor() {

    private val _wakeWordDetected = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
    val wakeWordDetected: SharedFlow<Unit> = _wakeWordDetected.asSharedFlow()

    private var isActive = false

    private val wakeWords = listOf("hey sona", "ok sona", "sona")

    /**
     * Starts listening for wake words.
     */
    fun start() {
        isActive = true
    }

    /**
     * Stops listening for wake words.
     */
    fun stop() {
        isActive = false
    }

    /**
     * Returns whether the detector is currently active.
     */
    fun isListening(): Boolean = isActive

    /**
     * Checks the given text for wake word matches.
     * Returns true if a wake word was detected and emits an event.
     */
    fun checkForWakeWord(text: String): Boolean {
        if (!isActive) return false
        val detected = wakeWords.any { text.lowercase().contains(it) }
        if (detected) {
            _wakeWordDetected.tryEmit(Unit)
        }
        return detected
    }
}
