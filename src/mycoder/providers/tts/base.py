"""
Base TTS Provider Class.
"""

from abc import ABC, abstractmethod
import logging
import asyncio
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class BaseTTSProvider(ABC):
    """Base class for TTS providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.voice = config.get("voice", "en")
        self.rate = config.get("rate", 150) # WPM or percent

    @abstractmethod
    async def speak(self, text: str) -> None:
        """Speak the text."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop current speech."""
        pass

    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """Return list of available voice IDs."""
        pass
