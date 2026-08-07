package com.sona.ai.features.voice

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Wrapper around Android's SpeechRecognizer API.
 * Provides a coroutine-based interface for speech-to-text.
 */
@Singleton
class SpeechRecognizerWrapper @Inject constructor(
    @ApplicationContext private val context: Context
) {

    private var speechRecognizer: SpeechRecognizer? = null

    /**
     * Checks if speech recognition is available on this device.
     */
    fun isAvailable(): Boolean =
        SpeechRecognizer.isRecognitionAvailable(context)

    /**
     * Starts listening and emits recognition results as a Flow.
     * Emits partial results as they come in, and completes with the final result.
     */
    fun startListening(languageCode: String = "en-US"): Flow<RecognitionResult> = callbackFlow {
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, languageCode)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }

        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                trySend(RecognitionResult.Ready)
            }

            override fun onBeginningOfSpeech() {
                trySend(RecognitionResult.SpeechStarted)
            }

            override fun onRmsChanged(rmsdB: Float) {
                trySend(RecognitionResult.AmplitudeChanged(rmsdB))
            }

            override fun onBufferReceived(buffer: ByteArray?) {}

            override fun onEndOfSpeech() {
                trySend(RecognitionResult.SpeechEnded)
            }

            override fun onError(error: Int) {
                trySend(RecognitionResult.Error(mapErrorCode(error)))
                close()
            }

            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull() ?: ""
                trySend(RecognitionResult.FinalResult(text))
                close()
            }

            override fun onPartialResults(partialResults: Bundle?) {
                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull() ?: ""
                if (text.isNotEmpty()) {
                    trySend(RecognitionResult.PartialResult(text))
                }
            }

            override fun onEvent(eventType: Int, params: Bundle?) {}
        })

        speechRecognizer?.startListening(intent)

        awaitClose {
            speechRecognizer?.stopListening()
            speechRecognizer?.destroy()
            speechRecognizer = null
        }
    }

    /**
     * Stops active listening.
     */
    fun stopListening() {
        speechRecognizer?.stopListening()
    }

    /**
     * Releases all resources.
     */
    fun destroy() {
        speechRecognizer?.destroy()
        speechRecognizer = null
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
        else -> "Unknown error ($error)"
    }
}

/**
 * Result types from speech recognition.
 */
sealed interface RecognitionResult {
    data object Ready : RecognitionResult
    data object SpeechStarted : RecognitionResult
    data object SpeechEnded : RecognitionResult
    data class AmplitudeChanged(val rmsDb: Float) : RecognitionResult
    data class PartialResult(val text: String) : RecognitionResult
    data class FinalResult(val text: String) : RecognitionResult
    data class Error(val message: String) : RecognitionResult
}
