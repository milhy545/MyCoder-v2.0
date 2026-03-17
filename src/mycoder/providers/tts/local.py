"""
Local TTS Providers (pyttsx3, espeak).
"""

import asyncio
import logging
import shutil
import subprocess
from typing import Any, Dict, List, Optional

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
        voice_id = self.config.get("voice_id")

        if not voice_id:
            voice_key = self.config.get("voice")
            if voice_key:
                voice_id = self._resolve_voice_id(voice_key)

        # Fallback to auto-detecting a Czech voice if not specified or not found
        if not voice_id:
            voice_id = self._detect_czech_voice()

        if voice_id:
            self.engine.setProperty("voice", voice_id)

    def _detect_czech_voice(self) -> Optional[str]:
        """Detect a Czech voice automatically based on language code or name."""
        voices = self.engine.getProperty("voices") or []
        czech_keywords = ["czech", "cesk", "česk", "cs", "cs-cz", "cs_cz", "405"]

        for voice in voices:
            name = str(getattr(voice, "name", "")).lower()
            if any(keyword in name for keyword in ["czech", "cesk", "česk"]):
                return getattr(voice, "id", None)

            languages = getattr(voice, "languages", [])
            if isinstance(languages, bytes):
                languages = [languages.decode("utf-8")]
            elif isinstance(languages, (list, tuple, set)):
                languages = [str(lang).lower() for lang in languages]
            else:
                languages = [str(languages).lower()]

            for language in languages:
                # Windows text-to-speech engine often uses language codes like '405' for Czech
                # Linux/espeak often uses 'cs' or 'cs-CZ'
                for kw in czech_keywords:
                    # strict matching for 'cs' or '405', substring for others
                    if language == kw or (kw not in ["cs", "405"] and kw in language):
                        return getattr(voice, "id", None)
        return None

    def _resolve_voice_id(self, voice_key: str) -> Optional[str]:
        """Resolve a configured voice key to a pyttsx3 voice id."""
        key = str(voice_key).lower()
        voices = self.engine.getProperty("voices") or []
        for voice in voices:
            voice_id = str(getattr(voice, "id", "")).lower()
            if key == voice_id:
                return getattr(voice, "id", None)
            name = str(getattr(voice, "name", "")).lower()
            if key in name:
                return getattr(voice, "id", None)
            languages = getattr(voice, "languages", [])
            if isinstance(languages, (list, tuple, set)):
                language_list = [str(lang).lower() for lang in languages]
            else:
                language_list = [str(languages).lower()]
            for language in language_list:
                if key in language:
                    return getattr(voice, "id", None)
        return None

    def speak_sync(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()

    async def speak(self, text: str) -> None:
        # pyttsx3 runAndWait is blocking, so run in thread
        await asyncio.to_thread(self.speak_sync, text)

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

    def speak_sync(self, text: str) -> None:
        args = [
            "espeak",
            "-v",
            self.config.get("voice", "en"),
            "-s",
            str(self.config.get("rate", 150)),
            text,
        ]
        subprocess.run(args)

    async def speak(self, text: str) -> None:
        await asyncio.to_thread(self.speak_sync, text)

    def stop(self) -> None:
        subprocess.run(["pkill", "espeak"])

    def get_available_voices(self) -> List[str]:
        return []
