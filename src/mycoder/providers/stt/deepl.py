"""
DeepL Provider (Voice/Translation).
Currently a placeholder as DeepL Voice API is in early access/limited.
"""

import logging
from typing import Optional, Dict, Any

from .base import BaseSTTProvider

logger = logging.getLogger(__name__)

class DeepLSTTProvider(BaseSTTProvider):
    """
    DeepL Voice Provider.

    NOTE: DeepL Voice is currently a separate product/beta.
    This provider serves as a placeholder structure for future integration
    or translation-based fallbacks.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        logger.warning("DeepL Voice API integration is not yet fully available/public.")
        logger.info("Please use Whisper, Gemini, or Azure for STT currently.")
        return None
