import sys
import types

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
    assert tts.provider == "pyttsx3"
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
    assert tts.provider == "espeak"


@pytest.mark.asyncio
async def test_speak_async_calls_sync(monkeypatch):
    tts = TTSEngine(provider="espeak")
    called = {"value": False}

    def fake_speak(text):
        called["value"] = True

    monkeypatch.setattr(tts, "_speak_sync", fake_speak)
    await tts.speak_async("test")
    assert called["value"] is True


def test_stop_pyttsx3(monkeypatch):
    engine = DummyEngine()
    fake_module = types.SimpleNamespace(init=lambda: engine)
    monkeypatch.setitem(sys.modules, "pyttsx3", fake_module)

    tts = TTSEngine(provider="pyttsx3", voice="cs", rate=150)
    tts.stop()
    assert engine.properties["stopped"] is True
