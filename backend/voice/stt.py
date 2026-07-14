"""Speech-to-Text engine — local Whisper-based transcription.

Supports:
- OpenAI Whisper (via whisper package)
- Faster-Whisper (CTranslate2 optimized)
- Whisper.cpp (via subprocess)

Falls back gracefully when providers are unavailable.
All processing is local — no cloud APIs, no data leaves the device.
"""

from __future__ import annotations

import time
import wave
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from config.logging import get_logger
from voice.schemas import STTProvider, TranscriptionResult

logger = get_logger(__name__)


class STTEngine(ABC):
    """Abstract Speech-to-Text engine."""

    provider: STTProvider

    @abstractmethod
    async def transcribe(self, audio_data: bytes, language: str = "en") -> TranscriptionResult:
        """Transcribe audio bytes to text."""

    @abstractmethod
    async def transcribe_file(self, file_path: Path, language: str = "en") -> TranscriptionResult:
        """Transcribe an audio file to text."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this STT provider is available."""


class WhisperSTT(STTEngine):
    """OpenAI Whisper local transcription.

    Uses the `whisper` or `faster-whisper` package for offline STT.
    Falls back to a simple echo mode if neither is installed.
    """

    provider = STTProvider.WHISPER

    def __init__(self, model_name: str = "base") -> None:
        self._model_name = model_name
        self._model: Any = None
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if Whisper is installed and usable."""
        if self._available is not None:
            return self._available
        try:
            import whisper  # noqa: F401

            self._available = True
        except ImportError:
            try:
                import faster_whisper  # noqa: F401

                self._available = True
            except ImportError:
                self._available = False
                logger.info(
                    "whisper_not_available",
                    hint="Install whisper: pip install openai-whisper or faster-whisper",
                )
        return self._available

    def _load_model(self) -> Any:
        """Load the Whisper model (lazy initialization)."""
        if self._model is not None:
            return self._model

        try:
            import whisper

            self._model = whisper.load_model(self._model_name)
            logger.info("whisper_model_loaded", model=self._model_name)
            return self._model
        except ImportError:
            pass

        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self._model_name, compute_type="int8")
            logger.info("faster_whisper_model_loaded", model=self._model_name)
            return self._model
        except ImportError:
            pass

        return None

    async def transcribe(self, audio_data: bytes, language: str = "en") -> TranscriptionResult:
        """Transcribe raw audio bytes.

        If Whisper is not available, returns a placeholder result indicating
        the audio was received but cannot be processed locally.
        """
        start = time.perf_counter()

        if not self.is_available():
            duration = len(audio_data) / (16000 * 2)  # Assume 16kHz 16-bit
            return TranscriptionResult(
                text="[Voice input received — Whisper not installed]",
                language=language,
                confidence=0.0,
                duration_seconds=duration,
                is_final=True,
            )

        model = self._load_model()
        if model is None:
            return TranscriptionResult(
                text="[Model not loaded]",
                language=language,
                confidence=0.0,
                duration_seconds=0.0,
                is_final=True,
            )

        # Write audio to temporary WAV for Whisper
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            _write_wav(tmp_path, audio_data)

        try:
            result = await self.transcribe_file(tmp_path, language)
        finally:
            tmp_path.unlink(missing_ok=True)

        result.duration_seconds = time.perf_counter() - start
        return result

    async def transcribe_file(self, file_path: Path, language: str = "en") -> TranscriptionResult:
        """Transcribe an audio file."""
        start = time.perf_counter()

        if not self.is_available():
            return TranscriptionResult(
                text="[Whisper not available]",
                language=language,
                confidence=0.0,
                duration_seconds=0.0,
                is_final=True,
            )

        model = self._load_model()
        if model is None:
            return TranscriptionResult(
                text="[Model not loaded]",
                language=language,
                confidence=0.0,
                is_final=True,
            )

        # Try faster-whisper first (returns segments)
        try:
            from faster_whisper import WhisperModel

            if isinstance(model, WhisperModel):
                segments, info = model.transcribe(str(file_path), language=language)
                text_parts = []
                seg_data = []
                for seg in segments:
                    text_parts.append(seg.text.strip())
                    seg_data.append(
                        {
                            "start": seg.start,
                            "end": seg.end,
                            "text": seg.text.strip(),
                        }
                    )
                return TranscriptionResult(
                    text=" ".join(text_parts),
                    language=info.language,
                    confidence=1.0 - (info.language_probability or 0.0),
                    duration_seconds=time.perf_counter() - start,
                    is_final=True,
                    segments=seg_data,
                )
        except (ImportError, AttributeError):
            pass

        # Fall back to standard whisper
        try:
            result = model.transcribe(str(file_path), language=language)
            return TranscriptionResult(
                text=result.get("text", "").strip(),
                language=result.get("language", language),
                confidence=0.9,
                duration_seconds=time.perf_counter() - start,
                is_final=True,
                segments=[
                    {"start": s["start"], "end": s["end"], "text": s["text"]}
                    for s in result.get("segments", [])
                ],
            )
        except Exception as exc:
            logger.error("whisper_transcribe_failed", error=str(exc))
            return TranscriptionResult(
                text=f"[Transcription error: {exc}]",
                language=language,
                confidence=0.0,
                duration_seconds=time.perf_counter() - start,
                is_final=True,
            )


class WhisperCppSTT(STTEngine):
    """Whisper.cpp integration via subprocess.

    Uses the whisper.cpp binary for fast CPU-based transcription.
    """

    provider = STTProvider.WHISPER_CPP

    def __init__(self, binary_path: str = "whisper-cpp", model_path: str = "") -> None:
        self._binary = binary_path
        self._model_path = model_path

    def is_available(self) -> bool:
        """Check if whisper.cpp binary exists."""
        import shutil

        return shutil.which(self._binary) is not None

    async def transcribe(self, audio_data: bytes, language: str = "en") -> TranscriptionResult:
        """Transcribe using whisper.cpp subprocess."""
        if not self.is_available():
            return TranscriptionResult(
                text="[whisper.cpp not installed]",
                language=language,
                confidence=0.0,
                is_final=True,
            )

        import asyncio
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            _write_wav(tmp_path, audio_data)

        try:
            cmd = [self._binary, "-f", str(tmp_path), "-l", language, "--no-timestamps"]
            if self._model_path:
                cmd.extend(["-m", self._model_path])

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            text = stdout.decode("utf-8", errors="replace").strip()
            return TranscriptionResult(
                text=text or "[No speech detected]",
                language=language,
                confidence=0.8 if text else 0.0,
                is_final=True,
            )
        except Exception as exc:
            logger.error("whisper_cpp_failed", error=str(exc))
            return TranscriptionResult(
                text=f"[whisper.cpp error: {exc}]",
                language=language,
                confidence=0.0,
                is_final=True,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def transcribe_file(self, file_path: Path, language: str = "en") -> TranscriptionResult:
        """Transcribe a file using whisper.cpp."""
        audio_data = file_path.read_bytes()
        return await self.transcribe(audio_data, language)


def _write_wav(path: Path, pcm_data: bytes, sample_rate: int = 16000, channels: int = 1) -> None:
    """Write raw PCM data as a WAV file."""
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
