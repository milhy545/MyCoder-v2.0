"""
Google STT Provider (Gemini).
"""

import logging
import os
import io
import time
from typing import Optional, Dict, Any

from .base import BaseSTTProvider

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GoogleSTTProvider(BaseSTTProvider):
    """Google STT using Gemini Multimodal."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
        self.model_name = config.get("model", "gemini-1.5-flash")

        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        if not GENAI_AVAILABLE or not self.model:
            logger.error("Gemini not available")
            return None

        try:
            # Gemini expects audio part
            # Currently genai SDK supports file uploads or inline data if small
            # For simplicity we try inline data logic if supported, or mocking via prompt
            # But wait, Gemini needs the audio blob.

            prompt = (
                f"Transcribe this audio exactly as spoken. "
                f"Language: {self.language}. "
                "Output ONLY the transcription text."
            )

            response = self.model.generate_content(
                [
                    prompt,
                    {"mime_type": "audio/wav", "data": audio_data}
                ]
            )

            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini STT failed: {e}")
            return None
