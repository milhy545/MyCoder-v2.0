import builtins
from unittest.mock import Mock, patch

import pytest

from mycoder.speech_tool import SpeechTool
from mycoder.tool_registry import ToolExecutionContext


@pytest.fixture
def execution_context(tmp_path):
    return ToolExecutionContext(mode="FULL", working_directory=tmp_path)


@pytest.fixture
def speech_tool():
    return SpeechTool()


@pytest.mark.asyncio
async def test_initialization(speech_tool, execution_context):
    assert speech_tool.name == "voice_dictation"
    assert speech_tool.is_running is False
    result = await speech_tool.execute(execution_context, mode="gui", action="status")
    assert result.success is True


@pytest.mark.asyncio
@patch("speech_recognition.dictation_app.GlobalDictationApp")
async def test_gui_mode_start_stop_status(
    mock_app_class, speech_tool, execution_context
):
    mock_app = Mock()
    mock_app.run.return_value = 0
    mock_app.get_status.return_value = {"state": "idle"}
    mock_app_class.return_value = mock_app

    result_start = await speech_tool.execute(
        execution_context, mode="gui", action="start"
    )
    assert result_start.success is True
    assert result_start.data["running"] is True

    result_status = await speech_tool.execute(
        execution_context, mode="gui", action="status"
    )
    assert result_status.data["app_status"] == {"state": "idle"}

    result_stop = await speech_tool.execute(
        execution_context, mode="gui", action="stop"
    )
    assert result_stop.data["running"] is False


@pytest.mark.asyncio
async def test_cli_mode_transcribe(monkeypatch, speech_tool, execution_context):
    mock_recorder = Mock()
    mock_recorder.start_recording.return_value = None
    mock_recorder.stop_recording.return_value = b"audio"

    mock_transcriber = Mock()
    mock_transcriber.transcribe.return_value = "hello"

    monkeypatch.setattr(
        "speech_recognition.audio_recorder.AudioRecorder",
        lambda *args, **kwargs: mock_recorder,
    )
    monkeypatch.setattr(
        "speech_recognition.whisper_transcriber.WhisperTranscriber",
        lambda *args, **kwargs: mock_transcriber,
    )
    monkeypatch.setattr("time.sleep", lambda *_: None)

    result = await speech_tool.execute(
        execution_context, mode="cli", duration=1, language="cs"
    )
    assert result.success is True
    assert result.data["text"] == "hello"


@pytest.mark.asyncio
async def test_validate_context_missing_dependency(
    monkeypatch, speech_tool, execution_context
):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "sounddevice":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    result = await speech_tool.validate_context(execution_context)
    assert result is False
