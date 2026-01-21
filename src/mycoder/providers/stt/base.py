"""
Base STT Provider Class.
"""

from abc import ABC, abstractmethod
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class BaseSTTProvider(ABC):
    """Base class for STT providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.language = config.get("language", "cs")

    @abstractmethod
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio data (wav bytes) to text.
        Blocking by default, can be wrapped in asyncio.to_thread.
        """
        pass
