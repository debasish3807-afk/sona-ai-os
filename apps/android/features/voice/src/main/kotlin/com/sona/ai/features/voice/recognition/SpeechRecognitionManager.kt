package com.sona.ai.features.voice.recognition

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Possible states for speech recognition.
 */
sealed interface RecognitionState {
    /** Recognition is idle and not listening. */
    data object Idle : RecognitionState

    /** Actively listening for speech input. */
    data object Listening : RecognitionState

    /** Partial recognition result received. */
    data class Partial(val text: String) : RecognitionState

    /** Final recognition result with confidence score. */
    data class Result(val text: String, val confidence: Float) : RecognitionState

    /** An error occurred during recognition. */
    data class Error(val code: Int, val message: String) : RecognitionState
}

/**
 * Enhanced speech recognition manager that provides a reactive state-based interface
 * for Android's SpeechRecognizer API. Supports both single-shot and continuous
 * recognition modes.
 */
@Singleton
class SpeechRecognitionManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    private val _state = MutableStateFlow<RecognitionState>(RecognitionState.Idle)
    val state: StateFlow<RecognitionState> = _state.asStateFlow()

    private var recognizer: SpeechRecognizer? = null
    private var isContinuous = false

    /**
     * Starts listening for speech input.
     * @param continuous If true, automatically restarts listening after each result.
     */
    fun startListening(continuous: Boolean = false) {
        isContinuous = continuous
        recognizer?.destroy()
        recognizer = SpeechRecognizer.createSpeechRecognizer(context)
        recognizer?.setRecognitionListener(createListener())

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }

        recognizer?.startListening(intent)
        _state.value = RecognitionState.Listening
    }

    /**
     * Stops listening and releases the recognizer.
     */
    fun stopListening() {
        isContinuous = false
        recognizer?.stopListening()
        recognizer?.destroy()
        recognizer = null
        _state.value = RecognitionState.Idle
    }

    /**
     * Returns whether speech recognition is available on this device.
     */
    fun isAvailable(): Boolean =
        SpeechRecognizer.isRecognitionAvailable(context)

    private fun createListener() = object : RecognitionListener {
        override fun onResults(results: Bundle?) {
            val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            val confidence = results?.getFloatArray(SpeechRecognizer.CONFIDENCE_SCORES)
            if (!matches.isNullOrEmpty()) {
                _state.value = RecognitionState.Result(
                    text = matches[0],
                    confidence = confidence?.firstOrNull() ?: 0f
                )
            }
            if (isContinuous) {
                startListening(true)
            }
        }

        override fun onPartialResults(partialResults: Bundle?) {
            val matches =
                partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            if (!matches.isNullOrEmpty()) {
                _state.value = RecognitionState.Partial(matches[0])
            }
        }

        override fun onError(error: Int) {
            _state.value = RecognitionState.Error(
                code = error,
                message = mapErrorCode(error)
            )
            if (isContinuous) {
                startListening(true)
            }
        }

        override fun onReadyForSpeech(params: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() {}
        override fun onEvent(eventType: Int, params: Bundle?) {}
    }

    private fun mapErrorCode(error: Int): String = when (error) {
        SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
        SpeechRecognizer.ERROR_CLIENT -> "Client error"
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Insufficient permissions"
        SpeechRecognizer.ERROR_NETWORK -> "Network error"
        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
        SpeechRecognizer.ERROR_NO_MATCH -> "No speech detected"
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognizer busy"
        SpeechRecognizer.ERROR_SERVER -> "Server error"
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Speech timeout"
        else -> "Unknown recognition error ($error)"
    }
}
