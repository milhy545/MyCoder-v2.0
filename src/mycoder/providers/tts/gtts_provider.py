"""
Google Translate TTS Provider.
"""
import asyncio
import logging
import os
import tempfile
from typing import Any, Dict, List

from .base import BaseTTSProvider

logger = logging.getLogger(__name__)


class GTTSProvider(BaseTTSProvider):
    """Google TTS (gTTS) Provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._current_process = None
        try:
            import gtts  # noqa: F401
        except ImportError:
            logger.error("gtts not installed")

    async def speak(self, text: str) -> None:
        from gtts import gTTS

        def _generate():
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tts = gTTS(text=text, lang=self.config.get("language", "en"))
                tts.save(tmp.name)
                return tmp.name

        path = await asyncio.to_thread(_generate)
        player = self._get_audio_player()
        if player:
            self._current_process = await asyncio.create_subprocess_exec(*player, path)
            await self._current_process.wait()
        try:
            os.unlink(path)
        except Exception as exc:
            logger.debug("Failed to remove temp audio file %s: %s", path, exc)

    def stop(self) -> None:
        if self._current_process:
            try:
                self._current_process.terminate()
            except Exception as e:
                logger.debug(f"Failed to terminate gTTS audio player: {e}")
            self._current_process = None

    def get_available_voices(self) -> List[str]:
        from gtts.lang import tts_langs

        return list(tts_langs().keys())

    def _get_audio_player(self) -> List[str]:
        import shutil

        if shutil.which("mpg123"):
            return ["mpg123", "-q"]
        if shutil.which("ffplay"):
            return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
        if shutil.which("afplay"):
            return ["afplay"]
        return None
