"""Tests for Voice AI Assistant (Phase 20.2)."""

from __future__ import annotations

import base64

import pytest

from voice.commands import detect_wake_word, recognize_command
from voice.engine import VoiceEngine
from voice.schemas import (
    STTProvider,
    SynthesisResult,
    TranscriptionResult,
    TTSProvider,
    VoiceCommand,
    VoiceMode,
    VoiceSettings,
)
from voice.stt import WhisperCppSTT, WhisperSTT
from voice.tts import CoquiTTS, PiperTTS, _generate_silence


class TestVoiceSchemas:
    """Test voice data models."""

    def test_voice_settings_defaults(self):
        s = VoiceSettings()
        assert s.stt_provider == STTProvider.WHISPER
        assert s.tts_provider == TTSProvider.PIPER
        assert s.voice_mode == VoiceMode.PUSH_TO_TALK
        assert s.language == "en"
        assert s.wake_word == "hey sona"
        assert s.wake_word_enabled is False

    def test_transcription_result(self):
        r = TranscriptionResult(text="hello world", confidence=0.95)
        assert r.text == "hello world"
        assert r.is_final is True
        assert r.segments == []

    def test_synthesis_result(self):
        r = SynthesisResult(audio_data=b"wav", sample_rate=22050)
        assert r.format == "wav"
        assert r.duration_seconds == 0.0

    def test_stt_provider_enum(self):
        assert STTProvider.WHISPER.value == "whisper"
        assert STTProvider.WHISPER_CPP.value == "whisper_cpp"

    def test_tts_provider_enum(self):
        assert TTSProvider.PIPER.value == "piper"
        assert TTSProvider.COQUI.value == "coqui"

    def test_voice_command_enum(self):
        assert VoiceCommand.OPEN_FILE.value == "open_file"
        assert VoiceCommand.STOP_SPEAKING.value == "stop_speaking"


class TestVoiceCommands:
    """Test voice command recognition."""

    def test_open_file(self):
        r = recognize_command("open file main.py")
        assert r.command == VoiceCommand.OPEN_FILE
        assert r.parameters["filename"] == "main.py"

    def test_search_project(self):
        r = recognize_command("search project for database")
        assert r.command == VoiceCommand.SEARCH_PROJECT
        assert "database" in r.parameters["query"]

    def test_start_research(self):
        r = recognize_command("research quantum computing")
        assert r.command == VoiceCommand.START_RESEARCH
        assert "quantum" in r.parameters["topic"]

    def test_open_terminal(self):
        r = recognize_command("open terminal")
        assert r.command == VoiceCommand.OPEN_TERMINAL

    def test_run_command(self):
        r = recognize_command("run command ls -la")
        assert r.command == VoiceCommand.RUN_COMMAND
        assert "ls" in r.parameters["command"]

    def test_github_search(self):
        r = recognize_command("search github for fastapi")
        assert r.command == VoiceCommand.GITHUB_SEARCH
        assert "fastapi" in r.parameters["query"]

    def test_memory_search(self):
        r = recognize_command("search memory for yesterday meeting")
        assert r.command == VoiceCommand.MEMORY_SEARCH

    def test_stop_speaking(self):
        r = recognize_command("stop speaking")
        assert r.command == VoiceCommand.STOP_SPEAKING

    def test_unknown_command(self):
        r = recognize_command("what is the weather today")
        assert r.command == VoiceCommand.UNKNOWN
        assert r.confidence == 0.0

    def test_empty_input(self):
        r = recognize_command("")
        assert r.command == VoiceCommand.UNKNOWN

    def test_wake_word_detected(self):
        assert detect_wake_word("hey sona what time is it") is True

    def test_wake_word_not_detected(self):
        assert detect_wake_word("hello world") is False

    def test_wake_word_custom(self):
        assert detect_wake_word("ok computer do this", "ok computer") is True


class TestWhisperSTT:
    """Test Whisper STT engine."""

    def test_whisper_availability(self):
        stt = WhisperSTT()
        # In CI without whisper installed, should be False
        available = stt.is_available()
        assert isinstance(available, bool)

    @pytest.mark.asyncio
    async def test_transcribe_fallback(self):
        stt = WhisperSTT()
        # With no whisper installed, should return fallback
        audio = b"\x00" * 32000  # 1 second of silence
        result = await stt.transcribe(audio)
        assert isinstance(result, TranscriptionResult)
        assert result.is_final is True
        assert isinstance(result.text, str)

    def test_whisper_cpp_availability(self):
        stt = WhisperCppSTT()
        available = stt.is_available()
        assert isinstance(available, bool)

    @pytest.mark.asyncio
    async def test_whisper_cpp_fallback(self):
        stt = WhisperCppSTT()
        audio = b"\x00" * 32000
        result = await stt.transcribe(audio)
        assert isinstance(result, TranscriptionResult)


class TestTTSEngines:
    """Test TTS engines."""

    def test_piper_availability(self):
        tts = PiperTTS()
        available = tts.is_available()
        assert isinstance(available, bool)

    def test_piper_list_voices(self):
        tts = PiperTTS()
        voices = tts.list_voices()
        assert len(voices) >= 3
        assert any("lessac" in v for v in voices)

    @pytest.mark.asyncio
    async def test_piper_synthesize_fallback(self):
        tts = PiperTTS()
        result = await tts.synthesize("Hello world")
        assert isinstance(result, SynthesisResult)
        assert len(result.audio_data) > 0
        assert result.sample_rate == 22050

    def test_coqui_availability(self):
        tts = CoquiTTS()
        available = tts.is_available()
        assert isinstance(available, bool)

    def test_coqui_list_voices(self):
        tts = CoquiTTS()
        voices = tts.list_voices()
        assert len(voices) >= 2

    @pytest.mark.asyncio
    async def test_coqui_synthesize_fallback(self):
        tts = CoquiTTS()
        result = await tts.synthesize("Hello")
        assert isinstance(result, SynthesisResult)
        assert len(result.audio_data) > 0

    def test_generate_silence(self):
        audio = _generate_silence(1.0)
        assert len(audio) > 44  # WAV header + data
        assert audio[:4] == b"RIFF"  # WAV magic bytes


class TestVoiceEngine:
    """Test voice engine orchestration."""

    @pytest.mark.asyncio
    async def test_transcribe(self):
        engine = VoiceEngine()
        audio = b"\x00" * 32000
        result = await engine.transcribe(audio)
        assert isinstance(result, TranscriptionResult)

    @pytest.mark.asyncio
    async def test_synthesize(self):
        engine = VoiceEngine()
        result = await engine.synthesize("Hello from Sona")
        assert isinstance(result, SynthesisResult)
        assert len(result.audio_data) > 0

    @pytest.mark.asyncio
    async def test_process_voice(self):
        engine = VoiceEngine()
        audio = b"\x00" * 32000
        result = await engine.process_voice(audio)
        assert "transcription" in result
        assert "action" in result

    def test_stop_speaking(self):
        engine = VoiceEngine()
        engine.stop_speaking()
        assert engine.is_speaking is False

    def test_get_stats(self):
        engine = VoiceEngine()
        stats = engine.get_stats()
        assert "transcriptions" in stats
        assert "syntheses" in stats
        assert "language" in stats

    def test_settings(self):
        settings = VoiceSettings(language="fr", wake_word="bonjour sona")
        engine = VoiceEngine(settings=settings)
        assert engine.settings.language == "fr"
        assert engine.settings.wake_word == "bonjour sona"

    @pytest.mark.asyncio
    async def test_wake_word_filtering(self):
        settings = VoiceSettings(wake_word_enabled=True, wake_word="hey sona")
        engine = VoiceEngine(settings=settings)
        audio = b"\x00" * 32000  # Will produce fallback text
        result = await engine.process_voice(audio)
        # Without real STT, the fallback text won't contain wake word
        assert result["action"] in ("ignored", "conversation", "command")


class TestVoiceAPI:
    """Test Voice API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from api.voice import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_transcribe_endpoint(self, client):
        audio_b64 = base64.b64encode(b"\x00" * 32000).decode()
        resp = client.post("/voice/transcribe", json={"audio_base64": audio_b64})
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        assert "confidence" in data

    def test_synthesize_endpoint(self, client):
        resp = client.post("/voice/synthesize", json={"text": "Hello Sona"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        assert len(resp.content) > 44

    def test_process_endpoint(self, client):
        audio_b64 = base64.b64encode(b"\x00" * 16000).decode()
        resp = client.post("/voice/process", json={"audio_base64": audio_b64})
        assert resp.status_code == 200
        assert "transcription" in resp.json()

    def test_status_endpoint(self, client):
        resp = client.get("/voice/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "transcriptions" in data
        assert "language" in data

    def test_settings_get(self, client):
        resp = client.get("/voice/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "en"
        assert data["wake_word"] == "hey sona"

    def test_settings_update(self, client):
        resp = client.patch("/voice/settings", json={"language": "fr"})
        assert resp.status_code == 200
        assert resp.json()["updated"] is True

    def test_voices_endpoint(self, client):
        resp = client.get("/voice/voices")
        assert resp.status_code == 200
        data = resp.json()
        assert "piper" in data
        assert "coqui" in data
