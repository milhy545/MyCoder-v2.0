"""
Google Translate TTS Provider.
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, List

from .base import BaseTTSProvider

logger = logging.getLogger(__name__)


class GTTSProvider(BaseTTSProvider):
    """Google TTS (gTTS) Provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import gtts
        except ImportError:
            logger.error("gtts not installed")

    def speak_sync(self, text: str) -> None:
        from gtts import gTTS

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tts = gTTS(text=text, lang=self.config.get("language", "en"))
            tts.save(tmp.name)
            path = tmp.name

        player = self._get_audio_player()
        if player:
            subprocess.run(player + [path])

        try:
            os.unlink(path)
        except Exception as exc:
            logger.debug("Failed to remove temp audio file %s: %s", path, exc)

    async def speak(self, text: str) -> None:
        await asyncio.to_thread(self.speak_sync, text)

    def stop(self) -> None:
        pass

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
