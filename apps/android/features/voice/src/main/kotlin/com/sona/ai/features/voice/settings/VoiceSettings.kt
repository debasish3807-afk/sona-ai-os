package com.sona.ai.features.voice.settings

import javax.inject.Inject
import javax.inject.Singleton

/**
 * Configuration data class for voice assistant settings.
 */
data class VoiceConfig(
    val wakeWordEnabled: Boolean = true,
    val continuousModeEnabled: Boolean = false,
    val speechRate: Float = 1.0f,
    val speechPitch: Float = 1.0f,
    val language: String = "en-US",
    val autoSendEnabled: Boolean = true,
    val silenceTimeout: Long = 2000L,
    val bluetoothPreferred: Boolean = false
)

/**
 * Manages voice-specific settings for the assistant.
 * Provides methods to update individual configuration values with
 * proper validation and bounds checking.
 */
@Singleton
class VoiceSettingsManager @Inject constructor() {

    private var _config = VoiceConfig()
    val config: VoiceConfig get() = _config

    /**
     * Updates the config using a transformation block.
     */
    fun update(block: VoiceConfig.() -> VoiceConfig) {
        _config = _config.block()
    }

    /**
     * Enables or disables wake word detection.
     */
    fun setWakeWord(enabled: Boolean) {
        _config = _config.copy(wakeWordEnabled = enabled)
    }

    /**
     * Enables or disables continuous listening mode.
     */
    fun setContinuousMode(enabled: Boolean) {
        _config = _config.copy(continuousModeEnabled = enabled)
    }

    /**
     * Sets the speech rate, clamped between 0.5 and 2.0.
     */
    fun setSpeechRate(rate: Float) {
        _config = _config.copy(speechRate = rate.coerceIn(0.5f, 2.0f))
    }

    /**
     * Sets the speech pitch, clamped between 0.5 and 2.0.
     */
    fun setSpeechPitch(pitch: Float) {
        _config = _config.copy(speechPitch = pitch.coerceIn(0.5f, 2.0f))
    }

    /**
     * Sets the recognition language code (e.g., "en-US", "es-ES").
     */
    fun setLanguage(language: String) {
        _config = _config.copy(language = language)
    }

    /**
     * Sets whether to prefer Bluetooth audio when available.
     */
    fun setBluetoothPreferred(preferred: Boolean) {
        _config = _config.copy(bluetoothPreferred = preferred)
    }

    /**
     * Sets the silence timeout in milliseconds before auto-stopping.
     */
    fun setSilenceTimeout(timeout: Long) {
        _config = _config.copy(silenceTimeout = timeout.coerceIn(500L, 10000L))
    }
}
