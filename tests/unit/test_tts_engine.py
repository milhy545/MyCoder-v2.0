import sys
import types
from unittest.mock import Mock, patch

import pytest

from mycoder.tts_engine import TTSEngine


class DummyVoice:
    def __init__(self, voice_id, name, languages):
        self.id = voice_id
        self.name = name
        self.languages = languages


class DummyEngine:
    def __init__(self):
        self.properties = {}

    def setProperty(self, key, value):
        self.properties[key] = value

    def getProperty(self, key):
        if key == "voices":
            return [DummyVoice("voice-cs", "Czech", ["cs"])]
        return None

    def say(self, text):
        self.properties["last_say"] = text

    def runAndWait(self):
        self.properties["ran"] = True

    def stop(self):
        self.properties["stopped"] = True


@pytest.mark.asyncio
async def test_pyttsx3_initialization(monkeypatch):
    engine = DummyEngine()
    fake_module = types.SimpleNamespace(init=lambda: engine)
    monkeypatch.setitem(sys.modules, "pyttsx3", fake_module)

    tts = TTSEngine(provider="pyttsx3", voice="cs", rate=160)
    assert tts.provider_name == "pyttsx3"
    assert engine.properties["rate"] == 160
    assert engine.properties["voice"] == "voice-cs"

    await tts.speak_async("Ahoj")
    assert engine.properties["last_say"] == "Ahoj"


def test_espeak_fallback(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pyttsx3":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/espeak")

    tts = TTSEngine(provider="pyttsx3", voice="cs", rate=150)
    assert tts.provider_name == "espeak"


@pytest.mark.asyncio
async def test_speak_async_calls_provider_speak(monkeypatch):
    tts = TTSEngine(provider="espeak")
    called = {"value": False}

    async def fake_speak(text):
        called["value"] = True

    monkeypatch.setattr(tts.provider, "speak", fake_speak)
    await tts.speak_async("test")
    assert called["value"] is True


def test_stop_pyttsx3(monkeypatch):
    engine = DummyEngine()
    fake_module = types.SimpleNamespace(init=lambda: engine)
    monkeypatch.setitem(sys.modules, "pyttsx3", fake_module)

    tts = TTSEngine(provider="pyttsx3", voice="cs", rate=150)
    tts.stop()
    assert engine.properties["stopped"] is True


@pytest.mark.asyncio
@patch("mycoder.tts_engine.GTTSProvider")
async def test_gtts_initialization(mock_gtts_class):
    mock_provider = Mock()
    from unittest.mock import AsyncMock

    mock_provider.speak = AsyncMock()
    mock_gtts_class.return_value = mock_provider

    tts = TTSEngine(provider="gtts")
    assert tts.provider_name == "gtts"

    await tts.speak_async("Hello")
    mock_provider.speak.assert_called_once_with("Hello")


@pytest.mark.asyncio
@patch("mycoder.tts_engine.AzureTTSProvider")
async def test_azure_initialization(mock_azure_class):
    mock_provider = Mock()
    from unittest.mock import AsyncMock

    mock_provider.speak = AsyncMock()
    mock_azure_class.return_value = mock_provider

    tts = TTSEngine(provider="azure")
    assert tts.provider_name == "azure"

    await tts.speak_async("Hello")
    mock_provider.speak.assert_called_once_with("Hello")


@pytest.mark.asyncio
@patch("mycoder.tts_engine.AmazonPollyProvider")
async def test_polly_initialization(mock_polly_class):
    mock_provider = Mock()
    from unittest.mock import AsyncMock

    mock_provider.speak = AsyncMock()
    mock_polly_class.return_value = mock_provider

    tts = TTSEngine(provider="polly")
    assert tts.provider_name == "polly"

    await tts.speak_async("Hello")
    mock_provider.speak.assert_called_once_with("Hello")


@pytest.mark.asyncio
@patch("mycoder.tts_engine.ElevenLabsProvider")
async def test_elevenlabs_initialization(mock_elevenlabs_class):
    mock_provider = Mock()
    from unittest.mock import AsyncMock

    mock_provider.speak = AsyncMock()
    mock_elevenlabs_class.return_value = mock_provider

    tts = TTSEngine(provider="elevenlabs")
    assert tts.provider_name == "elevenlabs"

    await tts.speak_async("Hello")
    mock_provider.speak.assert_called_once_with("Hello")
