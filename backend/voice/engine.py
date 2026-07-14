"""Voice Engine — orchestrates STT, TTS, and voice interaction.

Central coordinator for the voice assistant pipeline:
  Audio → STT → Command Recognition → AI Response → TTS → Audio
"""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from voice.commands import detect_wake_word, recognize_command
from voice.schemas import (
    SynthesisResult,
    TranscriptionResult,
    VoiceSettings,
)
from voice.stt import WhisperCppSTT, WhisperSTT
from voice.tts import CoquiTTS, PiperTTS

logger = get_logger(__name__)


class VoiceEngine:
    """Orchestrates the full voice interaction pipeline."""

    def __init__(self, settings: VoiceSettings | None = None) -> None:
        self._settings = settings or VoiceSettings()
        self._stt = WhisperSTT(model_name=self._settings.stt_model)
        self._stt_cpp = WhisperCppSTT()
        self._tts_piper = PiperTTS(
            voice=self._settings.voice_name,
            speed=self._settings.speech_speed,
        )
        self._tts_coqui = CoquiTTS()
        self._conversation: list[dict[str, str]] = []
        self._is_speaking = False
        self._stats = {"transcriptions": 0, "syntheses": 0, "commands": 0}

    @property
    def settings(self) -> VoiceSettings:
        return self._settings

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop_speaking(self) -> None:
        self._is_speaking = False

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """Transcribe audio using best available STT."""
        self._stats["transcriptions"] += 1
        lang = self._settings.language
        if self._stt.is_available():
            return await self._stt.transcribe(audio_data, language=lang)
        if self._stt_cpp.is_available():
            return await self._stt_cpp.transcribe(audio_data, language=lang)
        return TranscriptionResult(text="[No STT available]", language=lang)

    async def synthesize(self, text: str) -> SynthesisResult:
        """Synthesize text using best available TTS."""
        self._stats["syntheses"] += 1
        self._is_speaking = True
        try:
            if self._tts_piper.is_available():
                return await self._tts_piper.synthesize(text, self._settings.voice_name)
            if self._tts_coqui.is_available():
                return await self._tts_coqui.synthesize(text)
            return await self._tts_piper.synthesize(text)
        finally:
            self._is_speaking = False

    async def process_voice(self, audio_data: bytes) -> dict[str, Any]:
        """Full pipeline: transcribe → command check → respond."""
        result = await self.transcribe(audio_data)
        text = result.text

        # Wake word check
        if self._settings.wake_word_enabled:
            if not detect_wake_word(text, self._settings.wake_word):
                return {"transcription": text, "action": "ignored"}

        # Command recognition
        cmd = recognize_command(text)
        if cmd.command.value != "unknown":
            self._stats["commands"] += 1
            return {
                "transcription": text,
                "action": "command",
                "command": cmd.command.value,
                "parameters": cmd.parameters,
                "confidence": cmd.confidence,
            }

        # Conversation
        self._conversation.append({"role": "user", "content": text})
        return {"transcription": text, "action": "conversation", "message": text}

    def get_stats(self) -> dict[str, Any]:
        """Voice engine statistics."""
        return {
            **self._stats,
            "stt_available": self._stt.is_available(),
            "stt_cpp_available": self._stt_cpp.is_available(),
            "tts_piper_available": self._tts_piper.is_available(),
            "tts_coqui_available": self._tts_coqui.is_available(),
            "language": self._settings.language,
            "mode": self._settings.voice_mode.value,
        }
