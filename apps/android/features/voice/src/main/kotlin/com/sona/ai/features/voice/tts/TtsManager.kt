package com.sona.ai.features.voice.tts

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.suspendCancellableCoroutine
import java.util.Locale
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume

/**
 * Manages Text-to-Speech operations with queue support.
 * Provides a coroutine-friendly interface for speaking text and managing TTS configuration.
 */
@Singleton
class TtsManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    private var tts: TextToSpeech? = null
    private var isReady = false

    /**
     * Initializes the TTS engine. Must be called before speaking.
     */
    fun initialize() {
        tts = TextToSpeech(context) { status ->
            isReady = status == TextToSpeech.SUCCESS
            if (isReady) {
                tts?.language = Locale.US
            }
        }
    }

    /**
     * Speaks the given text and suspends until speech is complete.
     * Returns true if speech completed successfully, false otherwise.
     */
    suspend fun speak(text: String): Boolean = suspendCancellableCoroutine { cont ->
        if (!isReady || tts == null) {
            cont.resume(false)
            return@suspendCancellableCoroutine
        }

        val utteranceId = UUID.randomUUID().toString()

        tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(id: String?) {}

            override fun onDone(id: String?) {
                if (id == utteranceId && cont.isActive) {
                    cont.resume(true)
                }
            }

            @Deprecated("Deprecated in API")
            override fun onError(id: String?) {
                if (id == utteranceId && cont.isActive) {
                    cont.resume(false)
                }
            }

            override fun onError(utteranceId: String?, errorCode: Int) {
                if (utteranceId == utteranceId && cont.isActive) {
                    cont.resume(false)
                }
            }
        })

        tts?.speak(text, TextToSpeech.QUEUE_ADD, null, utteranceId)

        cont.invokeOnCancellation {
            tts?.stop()
        }
    }

    /**
     * Stops any active speech immediately.
     */
    fun stop() {
        tts?.stop()
    }

    /**
     * Sets the speech rate. Default is 1.0.
     * @param rate Speech rate between 0.5 and 2.0
     */
    fun setSpeed(rate: Float) {
        tts?.setSpeechRate(rate.coerceIn(0.5f, 2.0f))
    }

    /**
     * Sets the speech pitch. Default is 1.0.
     * @param pitch Pitch value between 0.5 and 2.0
     */
    fun setPitch(pitch: Float) {
        tts?.setPitch(pitch.coerceIn(0.5f, 2.0f))
    }

    /**
     * Returns whether the TTS engine is initialized and ready.
     */
    fun isInitialized(): Boolean = isReady

    /**
     * Releases all TTS resources.
     */
    fun shutdown() {
        tts?.shutdown()
        tts = null
        isReady = false
    }
}
