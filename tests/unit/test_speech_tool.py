import builtins
from unittest.mock import Mock, patch

import pytest

from mycoder.speech_tool import SpeechTool
from mycoder.tool_registry import ToolExecutionContext


class TestSpeechTool:
    @pytest.fixture
    def execution_context(self, tmp_path):
        return ToolExecutionContext(mode="FULL", working_directory=tmp_path)

    @pytest.fixture
    def speech_tool(self):
        return SpeechTool()

    def test_initialization(self, speech_tool):
        assert speech_tool.name == "voice_dictation"
        assert speech_tool.is_running is False

    @pytest.mark.asyncio
    @patch("speech_recognition.dictation_app.GlobalDictationApp")
    async def test_gui_mode_start(self, mock_app_class, speech_tool, execution_context):
        mock_app = Mock()
        mock_app_class.return_value = mock_app

        result = await speech_tool.execute(
            execution_context, mode="gui", action="start"
        )

        assert result.success is True
        assert result.data["running"] is True
        assert speech_tool.is_running is True
        mock_app_class.assert_called_once()

    @pytest.mark.asyncio
    @patch("speech_recognition.dictation_app.GlobalDictationApp")
    async def test_gui_mode_stop(self, mock_app_class, speech_tool, execution_context):
        mock_app = Mock()
        mock_app_class.return_value = mock_app

        # Start first
        await speech_tool.execute(execution_context, mode="gui", action="start")
        assert speech_tool.is_running is True

        # Then stop
        result = await speech_tool.execute(execution_context, mode="gui", action="stop")
        assert result.success is True
        assert result.data["running"] is False
        assert speech_tool.is_running is False
        mock_app.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_cli_mode_transcribe(
        self, monkeypatch, speech_tool, execution_context
    ):
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
        self, monkeypatch, speech_tool, execution_context
    ):
        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "sounddevice":
                raise ImportError("missing")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        result = await speech_tool.validate_context(execution_context)
        assert result is False
