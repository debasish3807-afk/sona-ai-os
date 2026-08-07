package com.sona.ai.features.voice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.domain.usecase.SendMessageUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Voice Chat screen.
 * Manages the STT → API → TTS cycle for voice-based interaction.
 */
@HiltViewModel
class VoiceViewModel @Inject constructor(
    private val speechRecognizer: SpeechRecognizerWrapper,
    private val ttsEngine: TextToSpeechEngine,
    private val sendMessageUseCase: SendMessageUseCase
) : ViewModel() {

    private val _state = MutableStateFlow<VoiceState>(VoiceState.Idle)
    val state: StateFlow<VoiceState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<VoiceEvent>()
    val events: SharedFlow<VoiceEvent> = _events.asSharedFlow()

    private var listeningJob: Job? = null
    private var speakingJob: Job? = null
    private var conversationId: String = "voice-session"

    init {
        initializeTts()
    }

    private fun initializeTts() {
        ttsEngine.initialize()
            .onEach { /* TTS ready */ }
            .catch { /* Ignore init errors, will handle when speaking */ }
            .launchIn(viewModelScope)
    }

    /**
     * Starts listening for user speech.
     */
    fun startListening() {
        if (!speechRecognizer.isAvailable()) {
            _state.value = VoiceState.Error("Speech recognition not available")
            return
        }

        listeningJob?.cancel()
        _state.value = VoiceState.Listening()

        listeningJob = speechRecognizer.startListening()
            .onEach { result ->
                when (result) {
                    is RecognitionResult.AmplitudeChanged -> {
                        _state.value = VoiceState.Listening(amplitude = result.rmsDb)
                    }
                    is RecognitionResult.PartialResult -> {
                        _state.value = VoiceState.Processing(transcribedText = result.text)
                    }
                    is RecognitionResult.FinalResult -> {
                        processTranscription(result.text)
                    }
                    is RecognitionResult.Error -> {
                        _state.value = VoiceState.Error(result.message)
                        _events.emit(VoiceEvent.ShowError(result.message))
                    }
                    else -> { /* Ignore other results */ }
                }
            }
            .catch { e ->
                _state.value = VoiceState.Error(e.message ?: "Recognition failed")
            }
            .launchIn(viewModelScope)
    }

    /**
     * Stops active listening.
     */
    fun stopListening() {
        listeningJob?.cancel()
        listeningJob = null
        speechRecognizer.stopListening()
        if (_state.value is VoiceState.Listening) {
            _state.value = VoiceState.Idle
        }
    }

    /**
     * Stops TTS playback.
     */
    fun stopSpeaking() {
        speakingJob?.cancel()
        speakingJob = null
        ttsEngine.stop()
        _state.value = VoiceState.Idle
    }

    /**
     * Processes transcribed text by sending to AI and speaking the response.
     */
    private fun processTranscription(text: String) {
        if (text.isBlank()) {
            _state.value = VoiceState.Idle
            return
        }

        _state.value = VoiceState.Processing(transcribedText = text)

        viewModelScope.launch {
            try {
                val response = sendMessageUseCase.execute(conversationId, text)
                speakResponse(response.content)
            } catch (e: Exception) {
                _state.value = VoiceState.Error(e.message ?: "Failed to get AI response")
                _events.emit(VoiceEvent.ShowError(e.message ?: "Failed to get response"))
            }
        }
    }

    /**
     * Speaks the AI response using TTS.
     */
    private fun speakResponse(text: String) {
        _state.value = VoiceState.Speaking(text = text)

        speakingJob = ttsEngine.speak(text)
            .onEach { status ->
                when (status) {
                    is TtsStatus.Done -> {
                        _state.value = VoiceState.Idle
                        _events.emit(VoiceEvent.VoiceSessionComplete)
                    }
                    is TtsStatus.Error -> {
                        _state.value = VoiceState.Error(status.message)
                    }
                    else -> { /* Speaking in progress */ }
                }
            }
            .catch { e ->
                _state.value = VoiceState.Error(e.message ?: "TTS failed")
            }
            .launchIn(viewModelScope)
    }

    override fun onCleared() {
        super.onCleared()
        speechRecognizer.destroy()
        ttsEngine.shutdown()
    }
}
