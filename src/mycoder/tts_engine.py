"""
Text-to-Speech Engine for MyCoder v2.1.1

Multi-backend TTS with Czech language support.
"""

import asyncio
import logging
import shutil
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Multi-backend Text-to-Speech engine.

    Supported providers:
    - pyttsx3: Offline, cross-platform (PRIMARY)
    - espeak: Linux native, Czech support
    - gtts: Google TTS (requires network)
    - gemini: Gemini TTS API (fallback)
    """

    def __init__(self, provider: str = "pyttsx3", voice: str = "cs", rate: int = 150):
        """
        Initialize TTS engine.

        Args:
            provider: TTS provider ("pyttsx3", "espeak", "gtts", "gemini")
            voice: Voice language code ("cs", "en", etc.)
            rate: Speech rate (words per minute)
        """
        self.provider = provider
        self.voice = voice
        self.rate = rate
        self.engine = None
        self._init_provider()

    def _init_provider(self) -> None:
        """Initialize TTS provider with fallback options."""
        provider_order = [self.provider] if self.provider else []
        for fallback in ["pyttsx3", "espeak", "gtts", "gemini"]:
            if fallback not in provider_order:
                provider_order.append(fallback)

        for candidate in provider_order:
            try:
                if candidate == "pyttsx3":
                    import pyttsx3

                    self.engine = pyttsx3.init()
                    self.provider = "pyttsx3"
                    self._configure_pyttsx3()
                    return
                if candidate == "espeak":
                    if not shutil.which("espeak"):
                        raise RuntimeError("espeak not available")
                    self.provider = "espeak"
                    self.engine = None
                    return
                if candidate == "gtts":
                    import gtts  # noqa: F401

                    if not self._get_audio_player():
                        raise RuntimeError("No audio player available for gtts")
                    self.provider = "gtts"
                    self.engine = None
                    return
                if candidate == "gemini":
                    raise RuntimeError("Gemini TTS not implemented")
            except Exception as exc:
                logger.warning(f"Failed to init {candidate}: {exc}")
                continue

        self.provider = "disabled"
        self.engine = None
        logger.error("No available TTS provider could be initialized")

    def _configure_pyttsx3(self) -> None:
        """Configure pyttsx3 engine for Czech."""
        if not self.engine:
            return

        self.engine.setProperty("rate", self.rate)

        try:
            voices = self.engine.getProperty("voices")
            target = self.voice.lower()
            for voice in voices:
                lang_match = False
                for lang in getattr(voice, "languages", []) or []:
                    if isinstance(lang, bytes):
                        lang = lang.decode("utf-8", errors="ignore")
                    if target in str(lang).lower():
                        lang_match = True
                        break
                name_match = target in str(getattr(voice, "name", "")).lower()
                if lang_match or name_match:
                    self.engine.setProperty("voice", voice.id)
                    return
        except Exception as exc:
            logger.warning(f"Failed to configure pyttsx3 voice: {exc}")

    async def speak_async(self, text: str) -> None:
        """
        Speak text asynchronously (non-blocking).

        Args:
            text: Text to speak
        """
        await asyncio.to_thread(self._speak_sync, text)

    def _speak_sync(self, text: str) -> None:
        """Synchronous speech (blocking)."""
        if self.provider == "pyttsx3" and self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
            return

        if self.provider == "espeak":
            args = ["espeak", "-v", self.voice, "-s", str(self.rate), text]
            subprocess.run(args, check=False)
            return

        if self.provider == "gtts":
            self._speak_gtts(text)
            return

        logger.error("TTS provider not available")

    def _get_audio_player(self) -> Optional[list[str]]:
        """Return a playback command for gtts audio if available."""
        if shutil.which("mpg123"):
            return ["mpg123", "-q"]
        if shutil.which("ffplay"):
            return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
        if shutil.which("afplay"):
            return ["afplay"]
        return None

    def _speak_gtts(self, text: str) -> None:
        """Speak using Google TTS and a local player."""
        try:
            from gtts import gTTS

            player = self._get_audio_player()
            if not player:
                logger.error("No audio player available for gtts output")
                return

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                gTTS(text=text, lang=self.voice).save(tmp.name)
                subprocess.run(player + [tmp.name], check=False)
        except Exception as exc:
            logger.error(f"gtts playback failed: {exc}")

    def stop(self) -> None:
        """Stop current speech."""
        if self.provider == "pyttsx3" and self.engine:
            self.engine.stop()
