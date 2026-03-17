"""
Base TTS Provider Class.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BaseTTSProvider(ABC):
    """Base class for TTS providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.voice = config.get("voice", "en")
        self.rate = config.get("rate", 150)  # WPM or percent

    @abstractmethod
    async def speak(self, text: str) -> None:
        """Speak the text asynchronously."""
        pass

    def speak_sync(self, text: str) -> None:
        """Speak the text synchronously (blocking).

        Subclasses should ideally override this with native synchronous implementations.
        """
        import asyncio
        import concurrent.futures

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            logger.warning(
                "speak_sync called from within an active event loop without native sync support."
            )
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                pool.submit(asyncio.run, self.speak(text)).result()
        else:
            asyncio.run(self.speak(text))

    @abstractmethod
    def stop(self) -> None:
        """Stop current speech."""
        pass

    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """Return list of available voice IDs."""
        pass
