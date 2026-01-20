"""
Speech Tool for MyCoder v2.1.1

Provides voice dictation capabilities as a MyCoder tool.
Modes: GUI overlay (background app) or CLI inline (record -> transcribe -> return).
"""

import asyncio
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple

from .tools.core import (
    BaseTool,
    ToolAvailability,
    ToolCapabilities,
    ToolCategory,
    ToolExecutionContext,
    ToolPriority,
    ToolResult,
)

logger = logging.getLogger(__name__)


class SpeechTool(BaseTool):
    """
    Hybrid voice dictation tool.

    Modes:
    - GUI: Launches GlobalDictationApp with overlay button (background)
    - CLI: Inline recording -> transcription -> text return (foreground)
    """

    def __init__(self):
        super().__init__(
            name="voice_dictation",
            category=ToolCategory.COMMUNICATION,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=ToolCapabilities(
                requires_filesystem=False,
                requires_network=True,
                max_execution_time=300,
                resource_intensive=True,
            ),
        )
        self.dictation_app = None
        self.app_thread: Optional[threading.Thread] = None
        self.is_running = False

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """
        Execute voice dictation.

        Args:
            mode (str): "gui" (overlay) or "cli" (inline). Default: "gui"
            action (str): "start", "stop", "status". Default: "start"
            duration (int): Recording duration in seconds (CLI mode). Default: 10
            language (str): Language code. Default: "cs"

        Returns:
            ToolResult with transcribed text (CLI mode) or status (GUI mode)
        """
        start_time = time.time()
        self.execution_count += 1
        mode = kwargs.get("mode", "gui")
        action = kwargs.get("action", "start")
        action_kwargs = dict(kwargs)
        action_kwargs.pop("action", None)

        try:
            if mode == "gui":
                result_data = await self._execute_gui_mode(action, **action_kwargs)
            elif mode == "cli":
                result_data = await self._execute_cli_mode(**kwargs)
            else:
                raise ValueError("Invalid mode: use 'gui' or 'cli'")

            duration_ms = int((time.time() - start_time) * 1000)
            self.total_execution_time += duration_ms
            self.last_execution = time.time()

            return ToolResult(
                success=True,
                data=result_data,
                tool_name=self.name,
                duration_ms=duration_ms,
            )

        except Exception as exc:
            self.error_count += 1
            duration_ms = int((time.time() - start_time) * 1000)
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=duration_ms,
                error=str(exc),
            )

    async def _execute_gui_mode(self, action: str, **kwargs) -> Dict[str, Any]:
        """Launch GUI overlay mode (background app)."""
        if action == "status":
            status = {
                "running": self.is_running,
                "app_status": None,
            }
            if self.dictation_app:
                try:
                    status["app_status"] = self.dictation_app.get_status()
                except Exception as exc:
                    status["app_status"] = {"error": str(exc)}
            return status

        if action == "start":
            if self.is_running:
                return {"running": True, "status": "already_running"}

            if self.dictation_app is None:
                from speech_recognition.dictation_app import GlobalDictationApp

                self.dictation_app = GlobalDictationApp(
                    language=kwargs.get("language", "cs"),
                    enable_gui=True,
                    enable_hotkeys=True,
                )

            if self.app_thread and self.app_thread.is_alive():
                return {"running": True, "status": "already_running"}

            def _run_app():
                try:
                    self.dictation_app.run()
                except Exception as exc:
                    logger.error(f"Dictation app failed: {exc}")
                    self.is_running = False

            self.app_thread = threading.Thread(target=_run_app, daemon=True)
            self.app_thread.start()
            self.is_running = True

            return {"running": True, "status": "started"}

        if action == "stop":
            if not self.dictation_app:
                self.is_running = False
                return {"running": False, "status": "not_running"}

            try:
                self.dictation_app.shutdown()
            finally:
                self.is_running = False
            return {"running": False, "status": "stopped"}

        raise ValueError("Invalid action: use 'start', 'stop', or 'status'")

    async def _execute_cli_mode(self, **kwargs) -> Dict[str, Any]:
        """Inline dictation: record -> transcribe -> return text."""
        duration = int(kwargs.get("duration", 10))
        language = kwargs.get("language", "cs")
        provider = kwargs.get("provider", "whisper_api")
        model = kwargs.get("model")

        text, provider_name = await asyncio.to_thread(
            self._record_and_transcribe,
            duration=duration,
            language=language,
            provider=provider,
            model=model,
        )

        if not text:
            raise RuntimeError("No transcription produced")

        return {
            "text": text,
            "provider": provider_name,
            "duration_seconds": duration,
        }

    def _record_and_transcribe(
        self,
        duration: int,
        language: str,
        provider: str,
        model: Optional[str],
    ) -> Tuple[Optional[str], str]:
        """Record audio and transcribe it using the requested provider."""
        from speech_recognition.audio_recorder import AudioRecorder
        from speech_recognition.gemini_transcriber import GeminiTranscriber
        from speech_recognition.whisper_transcriber import (
            WhisperProvider,
            WhisperTranscriber,
        )

        recorder = AudioRecorder(max_duration=duration)
        recorder.start_recording()
        time.sleep(max(1, duration))
        audio_data = recorder.stop_recording()

        if not audio_data:
            return None, provider

        provider = (provider or "whisper_api").lower()
        if provider in {"gemini", "gemini_api"}:
            transcriber = GeminiTranscriber(
                language=language, model=model or "gemini-1.5-flash"
            )
            text = transcriber.transcribe(audio_data)
            return text, "gemini"

        whisper_provider = (
            WhisperProvider.LOCAL
            if provider == "whisper_local"
            else WhisperProvider.API
        )
        transcriber = WhisperTranscriber(
            provider=whisper_provider,
            local_model=model or "base",
            language=language,
        )
        text = transcriber.transcribe(audio_data)
        return text, whisper_provider.value

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Validate speech tool can run."""
        try:
            import sounddevice  # noqa: F401

            return True
        except ImportError:
            logger.warning("Speech tool dependencies not installed")
            return False
