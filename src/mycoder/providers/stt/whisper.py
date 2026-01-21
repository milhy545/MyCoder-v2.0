"""
Whisper STT Provider (API & Local).
"""

import io
import logging
import os
import tempfile
from enum import Enum
from typing import Any, Dict, Optional

from .base import BaseSTTProvider

logger = logging.getLogger(__name__)

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    import whisper

    WHISPER_LOCAL_AVAILABLE = True
except ImportError:
    WHISPER_LOCAL_AVAILABLE = False
    whisper = None


class WhisperProviderType(Enum):
    API = "api"
    LOCAL = "local"


class WhisperSTTProvider(BaseSTTProvider):
    """Whisper STT Provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = WhisperProviderType(config.get("provider_type", "api"))
        self.model = config.get("model", "whisper-1")
        self.local_model_name = config.get("local_model", "base")
        self.temperature = config.get("temperature", 0.0)

        if self.provider_type == WhisperProviderType.API:
            self.api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not OPENAI_AVAILABLE or not self.api_key:
                logger.warning("OpenAI Whisper API not available")
            else:
                self.client = openai.OpenAI(api_key=self.api_key)

        elif self.provider_type == WhisperProviderType.LOCAL:
            if not WHISPER_LOCAL_AVAILABLE:
                logger.warning("Local Whisper not available")
                self.local_model = None
            else:
                logger.info(f"Loading local Whisper model: {self.local_model_name}")
                self.local_model = whisper.load_model(self.local_model_name)

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        if self.provider_type == WhisperProviderType.API:
            return self._transcribe_api(audio_data)
        elif self.provider_type == WhisperProviderType.LOCAL:
            return self._transcribe_local(audio_data)
        return None

    def _transcribe_api(self, audio_data: bytes) -> Optional[str]:
        if not OPENAI_AVAILABLE or not hasattr(self, "client"):
            return None
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=self.language,
                temperature=self.temperature,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Whisper API failed: {e}")
            return None

    def _transcribe_local(self, audio_data: bytes) -> Optional[str]:
        if not WHISPER_LOCAL_AVAILABLE or not self.local_model:
            return None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                result = self.local_model.transcribe(
                    tmp_path,
                    language=self.language,
                    temperature=self.temperature,
                    fp16=False,
                )
                return result["text"].strip()
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception as exc:
                    logger.debug(
                        "Failed to remove temp audio file %s: %s", tmp_path, exc
                    )
        except Exception as e:
            logger.error(f"Whisper Local failed: {e}")
            return None
