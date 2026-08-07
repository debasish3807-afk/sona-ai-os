package com.sona.ai.features.voice

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import java.util.Locale
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Wrapper around Android's TextToSpeech API.
 * Provides a coroutine-based interface for text-to-speech.
 */
@Singleton
class TextToSpeechEngine @Inject constructor(
    @ApplicationContext private val context: Context
) {

    private var tts: TextToSpeech? = null
    private var isInitialized = false

    /**
     * Initializes the TTS engine. Must be called before speaking.
     */
    fun initialize(): Flow<TtsStatus> = callbackFlow {
        tts = TextToSpeech(context) { status ->
            isInitialized = status == TextToSpeech.SUCCESS
            if (isInitialized) {
                tts?.language = Locale.US
                trySend(TtsStatus.Ready)
            } else {
                trySend(TtsStatus.Error("TTS initialization failed"))
                close()
            }
        }

        awaitClose {
            // Keep TTS alive for reuse
        }
    }

    /**
     * Speaks the given text and reports progress.
     */
    fun speak(text: String): Flow<TtsStatus> = callbackFlow {
        if (!isInitialized || tts == null) {
            trySend(TtsStatus.Error("TTS not initialized"))
            close()
            return@callbackFlow
        }

        val utteranceId = UUID.randomUUID().toString()

        tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(id: String?) {
                trySend(TtsStatus.Speaking(text))
            }

            override fun onDone(id: String?) {
                trySend(TtsStatus.Done)
                close()
            }

            @Deprecated("Deprecated in API")
            override fun onError(id: String?) {
                trySend(TtsStatus.Error("Speech error"))
                close()
            }

            override fun onError(utteranceId: String?, errorCode: Int) {
                trySend(TtsStatus.Error("Speech error: $errorCode"))
                close()
            }
        })

        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId)

        awaitClose {
            tts?.stop()
        }
    }

    /**
     * Stops any active speech.
     */
    fun stop() {
        tts?.stop()
    }

    /**
     * Releases all resources.
     */
    fun shutdown() {
        tts?.shutdown()
        tts = null
        isInitialized = false
    }
}

/**
 * Status updates from the TTS engine.
 */
sealed interface TtsStatus {
    data object Ready : TtsStatus
    data class Speaking(val text: String) : TtsStatus
    data object Done : TtsStatus
    data class Error(val message: String) : TtsStatus
}
