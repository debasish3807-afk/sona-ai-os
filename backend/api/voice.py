"""Voice AI API — endpoints for speech interaction.

Provides:
- POST /voice/transcribe — STT (audio → text)
- POST /voice/synthesize — TTS (text → audio)
- POST /voice/process — Full voice pipeline
- GET /voice/status — Engine availability
- GET /voice/settings — Voice settings
- PATCH /voice/settings — Update settings
- GET /voice/voices — List available voices
"""

from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

from config.logging import get_logger
from voice.engine import VoiceEngine

logger = get_logger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

_engine = VoiceEngine()


class TranscribeRequest(BaseModel):
    """Audio transcription request."""

    audio_base64: str = Field(..., description="Base64-encoded audio (16kHz 16-bit PCM or WAV)")
    language: str = "en"


class SynthesizeRequest(BaseModel):
    """Text synthesis request."""

    text: str = Field(..., min_length=1)
    voice: str = ""


class ProcessRequest(BaseModel):
    """Full voice processing request."""

    audio_base64: str = Field(..., description="Base64-encoded audio")


class VoiceSettingsUpdate(BaseModel):
    """Voice settings update."""

    language: str = ""
    voice_name: str = ""
    speech_speed: float | None = None
    volume: float | None = None
    wake_word: str = ""
    wake_word_enabled: bool | None = None
    noise_suppression: bool | None = None


@router.post("/transcribe")
async def transcribe(request: TranscribeRequest) -> dict[str, Any]:
    """Transcribe audio to text using local Whisper."""
    audio_data = base64.b64decode(request.audio_base64)
    result = await _engine.transcribe(audio_data)
    return {
        "text": result.text,
        "language": result.language,
        "confidence": result.confidence,
        "is_final": result.is_final,
        "duration_seconds": result.duration_seconds,
    }


@router.post("/synthesize")
async def synthesize(request: SynthesizeRequest) -> Response:
    """Synthesize text to speech audio (returns WAV)."""
    result = await _engine.synthesize(request.text)
    return Response(
        content=result.audio_data,
        media_type="audio/wav",
        headers={
            "X-Duration-Seconds": str(result.duration_seconds),
            "X-Sample-Rate": str(result.sample_rate),
        },
    )


@router.post("/process")
async def process_voice(request: ProcessRequest) -> dict[str, Any]:
    """Full voice pipeline: transcribe → recognize → respond."""
    audio_data = base64.b64decode(request.audio_base64)
    return await _engine.process_voice(audio_data)


@router.get("/status")
async def voice_status() -> dict[str, Any]:
    """Get voice engine status and availability."""
    return _engine.get_stats()


@router.get("/settings")
async def get_voice_settings() -> dict[str, Any]:
    """Get current voice settings."""
    s = _engine.settings
    return {
        "language": s.language,
        "voice_name": s.voice_name,
        "speech_speed": s.speech_speed,
        "volume": s.volume,
        "wake_word": s.wake_word,
        "wake_word_enabled": s.wake_word_enabled,
        "noise_suppression": s.noise_suppression,
        "echo_cancellation": s.echo_cancellation,
        "voice_mode": s.voice_mode.value,
        "stt_provider": s.stt_provider.value,
        "tts_provider": s.tts_provider.value,
    }


@router.patch("/settings")
async def update_voice_settings(update: VoiceSettingsUpdate) -> dict[str, Any]:
    """Update voice settings."""
    s = _engine.settings
    if update.language:
        s.language = update.language
    if update.voice_name:
        s.voice_name = update.voice_name
    if update.speech_speed is not None:
        s.speech_speed = update.speech_speed
    if update.volume is not None:
        s.volume = update.volume
    if update.wake_word:
        s.wake_word = update.wake_word
    if update.wake_word_enabled is not None:
        s.wake_word_enabled = update.wake_word_enabled
    if update.noise_suppression is not None:
        s.noise_suppression = update.noise_suppression
    return {"updated": True}


@router.get("/voices")
async def list_voices() -> dict[str, Any]:
    """List available TTS voices."""
    return {
        "piper": _engine._tts_piper.list_voices(),
        "coqui": _engine._tts_coqui.list_voices(),
    }
