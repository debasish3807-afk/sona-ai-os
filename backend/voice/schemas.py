"""Voice AI schemas and data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class STTProvider(str, Enum):
    """Supported Speech-to-Text providers."""

    WHISPER = "whisper"
    FASTER_WHISPER = "faster_whisper"
    WHISPER_CPP = "whisper_cpp"


class TTSProvider(str, Enum):
    """Supported Text-to-Speech providers."""

    PIPER = "piper"
    COQUI = "coqui"


class VoiceMode(str, Enum):
    """Voice interaction mode."""

    PUSH_TO_TALK = "push_to_talk"
    CONTINUOUS = "continuous"
    WAKE_WORD = "wake_word"


class VoiceCommand(str, Enum):
    """Recognized voice commands."""

    OPEN_FILE = "open_file"
    SEARCH_PROJECT = "search_project"
    START_RESEARCH = "start_research"
    READ_DOCUMENT = "read_document"
    OPEN_TERMINAL = "open_terminal"
    RUN_COMMAND = "run_command"
    GITHUB_SEARCH = "github_search"
    MEMORY_SEARCH = "memory_search"
    STOP_SPEAKING = "stop_speaking"
    UNKNOWN = "unknown"


@dataclass
class TranscriptionResult:
    """Result from speech-to-text."""

    text: str
    language: str = "en"
    confidence: float = 0.0
    duration_seconds: float = 0.0
    is_final: bool = True
    segments: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SynthesisResult:
    """Result from text-to-speech."""

    audio_data: bytes = b""
    sample_rate: int = 22050
    duration_seconds: float = 0.0
    format: str = "wav"


@dataclass
class VoiceSettings:
    """Voice assistant configuration."""

    stt_provider: STTProvider = STTProvider.WHISPER
    tts_provider: TTSProvider = TTSProvider.PIPER
    voice_mode: VoiceMode = VoiceMode.PUSH_TO_TALK
    language: str = "en"
    voice_name: str = "default"
    speech_speed: float = 1.0
    pitch: float = 1.0
    volume: float = 0.8
    wake_word: str = "hey sona"
    wake_word_enabled: bool = False
    noise_suppression: bool = True
    echo_cancellation: bool = True
    stt_model: str = "base"
    silence_threshold: float = 0.3
    max_recording_seconds: float = 30.0


@dataclass
class VoiceCommandResult:
    """Result of voice command recognition."""

    command: VoiceCommand
    parameters: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str = ""
