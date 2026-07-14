"""Text-to-Speech engine — local voice synthesis.

Supports:
- Piper TTS (fast, lightweight, offline)
- Coqui TTS (high quality, more resource intensive)

All processing is local — no cloud APIs.
"""

from __future__ import annotations

import asyncio
import struct
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from config.logging import get_logger
from voice.schemas import SynthesisResult, TTSProvider

logger = get_logger(__name__)


class TTSEngine(ABC):
    """Abstract Text-to-Speech engine."""

    provider: TTSProvider

    @abstractmethod
    async def synthesize(self, text: str, voice: str = "default") -> SynthesisResult:
        """Synthesize text to audio bytes."""

    @abstractmethod
    def list_voices(self) -> list[str]:
        """List available voices."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this TTS provider is available."""


class PiperTTS(TTSEngine):
    """Piper TTS — fast, lightweight, offline text-to-speech.

    Uses the piper-tts binary or piper Python package.
    Models are ONNX-based and run efficiently on CPU.
    """

    provider = TTSProvider.PIPER

    def __init__(
        self,
        model_path: str = "",
        voice: str = "en_US-lessac-medium",
        speed: float = 1.0,
    ) -> None:
        self._model_path = model_path
        self._default_voice = voice
        self._speed = speed
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if Piper is installed."""
        if self._available is not None:
            return self._available
        try:
            import shutil

            if shutil.which("piper"):
                self._available = True
                return True
        except Exception:
            pass

        try:
            import piper  # noqa: F401

            self._available = True
        except ImportError:
            self._available = False
            logger.info("piper_not_available", hint="Install: pip install piper-tts")
        return self._available

    def list_voices(self) -> list[str]:
        """List available Piper voices."""
        return [
            "en_US-lessac-medium",
            "en_US-amy-medium",
            "en_US-ryan-medium",
            "en_GB-alan-medium",
            "en_GB-jenny-medium",
        ]

    async def synthesize(self, text: str, voice: str = "") -> SynthesisResult:
        """Synthesize text using Piper TTS.

        Returns WAV audio data. Falls back to silence if Piper unavailable.
        """
        start = time.perf_counter()
        voice = voice or self._default_voice

        if not self.is_available():
            # Return minimal valid WAV (silence) as fallback
            return SynthesisResult(
                audio_data=_generate_silence(0.5),
                sample_rate=22050,
                duration_seconds=0.5,
                format="wav",
            )

        try:
            # Try piper binary first
            import shutil

            if shutil.which("piper"):
                return await self._synthesize_binary(text, voice)
        except Exception:
            pass

        # Try piper Python package
        try:
            return await self._synthesize_python(text, voice)
        except Exception as exc:
            logger.error("piper_synthesis_failed", error=str(exc))
            return SynthesisResult(
                audio_data=_generate_silence(0.5),
                sample_rate=22050,
                duration_seconds=time.perf_counter() - start,
                format="wav",
            )

    async def _synthesize_binary(self, text: str, voice: str) -> SynthesisResult:
        """Synthesize using piper CLI binary."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        cmd = ["piper", "--model", voice, "--output_file", str(tmp_path)]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate(input=text.encode("utf-8"))

        try:
            audio_data = tmp_path.read_bytes()
            duration = len(audio_data) / (22050 * 2)
            return SynthesisResult(
                audio_data=audio_data,
                sample_rate=22050,
                duration_seconds=duration,
                format="wav",
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def _synthesize_python(self, text: str, voice: str) -> SynthesisResult:
        """Synthesize using piper Python package."""
        import piper

        tts = piper.PiperVoice.load(voice)
        audio = tts.synthesize(text)
        return SynthesisResult(
            audio_data=bytes(audio),
            sample_rate=22050,
            duration_seconds=len(audio) / (22050 * 2),
            format="wav",
        )


class CoquiTTS(TTSEngine):
    """Coqui TTS — high-quality neural text-to-speech.

    More resource-intensive than Piper but produces more natural speech.
    """

    provider = TTSProvider.COQUI

    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC") -> None:
        self._model_name = model_name
        self._tts: Any = None
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if Coqui TTS is installed."""
        if self._available is not None:
            return self._available
        try:
            from TTS.api import TTS  # noqa: F401

            self._available = True
        except ImportError:
            self._available = False
            logger.info("coqui_not_available", hint="Install: pip install TTS")
        return self._available

    def list_voices(self) -> list[str]:
        """List available Coqui models/voices."""
        return [
            "tts_models/en/ljspeech/tacotron2-DDC",
            "tts_models/en/ljspeech/glow-tts",
            "tts_models/en/vctk/vits",
        ]

    async def synthesize(self, text: str, voice: str = "") -> SynthesisResult:
        """Synthesize using Coqui TTS."""
        if not self.is_available():
            return SynthesisResult(
                audio_data=_generate_silence(0.5),
                sample_rate=22050,
                duration_seconds=0.5,
                format="wav",
            )

        try:
            from TTS.api import TTS

            if self._tts is None:
                self._tts = TTS(model_name=voice or self._model_name)

            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            self._tts.tts_to_file(text=text, file_path=str(tmp_path))
            audio_data = tmp_path.read_bytes()
            tmp_path.unlink(missing_ok=True)

            return SynthesisResult(
                audio_data=audio_data,
                sample_rate=22050,
                duration_seconds=len(audio_data) / (22050 * 2),
                format="wav",
            )
        except Exception as exc:
            logger.error("coqui_synthesis_failed", error=str(exc))
            return SynthesisResult(
                audio_data=_generate_silence(0.5),
                sample_rate=22050,
                duration_seconds=0.5,
                format="wav",
            )


def _generate_silence(duration_seconds: float, sample_rate: int = 22050) -> bytes:
    """Generate silent WAV audio data."""
    num_samples = int(sample_rate * duration_seconds)
    # PCM 16-bit silence
    pcm_data = struct.pack(f"<{num_samples}h", *([0] * num_samples))
    # Create WAV header + data
    import io
    import wave

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buffer.getvalue()
