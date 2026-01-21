"""
Local TTS Providers (pyttsx3, espeak).
"""

import logging
import asyncio
import shutil
import subprocess
from typing import List, Dict, Any

from .base import BaseTTSProvider

logger = logging.getLogger(__name__)


class Pyttsx3Provider(BaseTTSProvider):
    """Offline TTS using pyttsx3."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        import pyttsx3
        self.engine = pyttsx3.init()
        self._configure()

    def _configure(self):
        self.engine.setProperty("rate", self.config.get("rate", 150))
        # Attempt to set voice
        voice_id = self.config.get("voice_id")
        if voice_id:
            self.engine.setProperty("voice", voice_id)

    async def speak(self, text: str) -> None:
        # pyttsx3 runAndWait is blocking, so run in thread
        def _speak():
            self.engine.say(text)
            self.engine.runAndWait()

        await asyncio.to_thread(_speak)

    def stop(self) -> None:
        self.engine.stop()

    def get_available_voices(self) -> List[str]:
        return [v.id for v in self.engine.getProperty("voices")]


class EspeakProvider(BaseTTSProvider):
    """Linux native espeak."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not shutil.which("espeak"):
            logger.warning("espeak not found")

    async def speak(self, text: str) -> None:
        args = ["espeak", "-v", self.config.get("voice", "en"), "-s", str(self.config.get("rate", 150)), text]
        await asyncio.to_thread(subprocess.run, args)

    def stop(self) -> None:
        subprocess.run(["pkill", "espeak"])

    def get_available_voices(self) -> List[str]:
        return []
