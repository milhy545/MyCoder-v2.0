"""
Text-to-Speech Engine for MyCoder v2.2.0

Multi-backend TTS with support for:
- pyttsx3 (Offline)
- espeak (Linux Native)
- gTTS (Google Translate)
- Azure Speech
- Amazon Polly
- ElevenLabs
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .providers.tts.local import Pyttsx3Provider, EspeakProvider
from .providers.tts.gtts_provider import GTTSProvider
from .providers.tts.azure import AzureTTSProvider
from .providers.tts.polly import AmazonPollyProvider
from .providers.tts.elevenlabs import ElevenLabsProvider
from .providers.tts.base import BaseTTSProvider

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Multi-backend Text-to-Speech engine.
    """

    def __init__(
        self,
        provider: str = "pyttsx3",
        config: Optional[Dict[str, Any]] = None,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
    ):
        """
        Initialize TTS engine.

        Args:
            provider: TTS provider name
            config: Configuration dictionary
            voice: Preferred voice or language identifier
            rate: Speech rate
        """
        self.provider_name = provider
        self.config = dict(config or {})
        if voice is not None:
            self.config["voice"] = voice
        if rate is not None:
            self.config["rate"] = rate
        self.config.setdefault("rate", 150)

        self.provider: Optional[BaseTTSProvider] = None
        self._init_provider()

    def _init_provider(self) -> None:
        """Initialize TTS provider with fallback options."""
        # Try primary
        if self._try_init(self.provider_name):
            return

        # Fallbacks
        fallbacks = ["pyttsx3", "espeak", "gtts"]
        for fallback in fallbacks:
            if fallback != self.provider_name:
                if self._try_init(fallback):
                    logger.info(f"Fallback to TTS provider: {fallback}")
                    self.provider_name = fallback
                    return

        logger.error("No available TTS provider could be initialized")

    def _try_init(self, name: str) -> bool:
        try:
            if name == "pyttsx3":
                self.provider = Pyttsx3Provider(self.config)
            elif name == "espeak":
                self.provider = EspeakProvider(self.config)
            elif name == "gtts":
                self.provider = GTTSProvider(self.config)
            elif name == "azure":
                self.provider = AzureTTSProvider(self.config)
            elif name == "polly":
                self.provider = AmazonPollyProvider(self.config)
            elif name == "elevenlabs":
                self.provider = ElevenLabsProvider(self.config)
            else:
                return False
            return True
        except Exception as e:
            logger.warning(f"Failed to init TTS provider {name}: {e}")
            return False

    async def speak_async(self, text: str) -> None:
        """Speak text asynchronously."""
        if not self.provider:
            return
        result = self._speak_sync(text)
        if asyncio.iscoroutine(result):
            _ = await result

    def _speak_sync(self, text: str):
        """Internal helper for speaking text."""
        if not self.provider:
            return None
        return self.provider.speak(text)

    def stop(self) -> None:
        """Stop current speech."""
        if self.provider:
            self.provider.stop()
