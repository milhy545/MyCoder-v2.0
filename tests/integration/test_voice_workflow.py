import sys
import types
from unittest.mock import Mock, patch

import pytest

from mycoder.speech_tool import SpeechTool
from mycoder.tool_registry import ToolExecutionContext
from mycoder.tts_engine import TTSEngine


@pytest.mark.asyncio
@patch("speech_recognition.dictation_app.GlobalDictationApp")
async def test_voice_start_and_tts(mock_app_class, tmp_path, monkeypatch):
    mock_app = Mock()
    mock_app.run.return_value = 0
    mock_app.get_status.return_value = {"state": "idle"}
    mock_app_class.return_value = mock_app

    tool = SpeechTool()
    context = ToolExecutionContext(mode="FULL", working_directory=tmp_path)

    result = await tool.execute(context, mode="gui", action="start")
    assert result.success is True

    engine = Mock()
    fake_module = types.SimpleNamespace(init=lambda: engine)
    monkeypatch.setitem(sys.modules, "pyttsx3", fake_module)

    def fake_get_property(key):
        if key == "voices":
            voice = Mock()
            voice.id = "voice-cs"
            voice.name = "Czech"
            voice.languages = ["cs"]
            return [voice]
        return None

    engine.getProperty.side_effect = fake_get_property

    tts = TTSEngine(provider="pyttsx3", voice="cs", rate=150)
    await tts.speak_async("Ahoj")
    engine.say.assert_called_once()
