"""
Whisper-based speech transcription module.

Supports both OpenAI Whisper API and local Whisper models.
"""

import io
import logging
import os
from enum import Enum
from typing import Optional, Dict, Any
import tempfile

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

logger = logging.getLogger(__name__)


class WhisperProvider(Enum):
    """Available Whisper transcription providers."""
    API = "api"
    LOCAL = "local"


class WhisperTranscriber:
    """
    Transcribes audio using OpenAI Whisper.

    Supports both API-based and local model-based transcription with automatic fallback.
    """

    def __init__(
        self,
        provider: WhisperProvider = WhisperProvider.API,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        local_model: str = "base",
        language: str = "cs",
        temperature: float = 0.0,
    ):
        """
        Initialize the Whisper transcriber.

        Args:
            provider: Transcription provider (API or LOCAL)
            api_key: OpenAI API key (for API provider)
            model: Whisper model name for API (default: "whisper-1")
            local_model: Local Whisper model size (tiny, base, small, medium, large)
            language: Language code for transcription (default: "cs" for Czech)
            temperature: Sampling temperature (0.0 = deterministic)
        """
        self.provider = provider
        self.model = model
        self.local_model_name = local_model
        self.language = language
        self.temperature = temperature

        # Initialize API client if using API provider
        if provider == WhisperProvider.API:
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "OpenAI API requires openai package. "
                    "Install with: poetry install --extras speech"
                )

            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                    "or pass api_key parameter"
                )

            self.client = openai.OpenAI(api_key=api_key)
            self.local_model = None
            logger.info(f"Initialized Whisper API transcriber with model {model}")

        # Initialize local model if using local provider
        elif provider == WhisperProvider.LOCAL:
            if not WHISPER_LOCAL_AVAILABLE:
                raise ImportError(
                    "Local Whisper requires openai-whisper package. "
                    "Install with: poetry install --extras speech"
                )

            logger.info(f"Loading local Whisper model: {local_model}")
            self.local_model = whisper.load_model(local_model)
            self.client = None
            logger.info(f"Loaded local Whisper model: {local_model}")

        else:
            raise ValueError(f"Unknown provider: {provider}")

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Audio data in WAV format

        Returns:
            Transcribed text, or None if transcription failed
        """
        if self.provider == WhisperProvider.API:
            return self._transcribe_api(audio_data)
        elif self.provider == WhisperProvider.LOCAL:
            return self._transcribe_local(audio_data)
        else:
            logger.error(f"Unknown provider: {self.provider}")
            return None

    def _transcribe_api(self, audio_data: bytes) -> Optional[str]:
        """Transcribe using OpenAI Whisper API."""
        try:
            # Create a temporary file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            # Call Whisper API
            logger.info(f"Transcribing audio via API (model: {self.model})")
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=self.language,
                temperature=self.temperature,
            )

            text = response.text.strip()
            logger.info(f"Transcription successful: {len(text)} characters")
            return text

        except Exception as e:
            logger.error(f"API transcription failed: {e}")
            return None

    def _transcribe_local(self, audio_data: bytes) -> Optional[str]:
        """Transcribe using local Whisper model."""
        try:
            # Save audio to temporary file (Whisper requires file path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            try:
                # Transcribe with local model
                logger.info(f"Transcribing audio locally (model: {self.local_model_name})")
                result = self.local_model.transcribe(
                    tmp_path,
                    language=self.language,
                    temperature=self.temperature,
                    fp16=False,  # Use FP32 for CPU compatibility
                )

                text = result["text"].strip()
                logger.info(f"Transcription successful: {len(text)} characters")
                return text

            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")

        except Exception as e:
            logger.error(f"Local transcription failed: {e}")
            return None

    def transcribe_with_fallback(
        self,
        audio_data: bytes,
        fallback_provider: Optional[WhisperProvider] = None,
    ) -> Optional[str]:
        """
        Transcribe with automatic fallback to alternative provider.

        Args:
            audio_data: Audio data in WAV format
            fallback_provider: Provider to use if primary fails (default: opposite of current)

        Returns:
            Transcribed text, or None if all attempts failed
        """
        # Try primary provider
        text = self.transcribe(audio_data)
        if text:
            return text

        # Determine fallback provider
        if fallback_provider is None:
            fallback_provider = (
                WhisperProvider.LOCAL
                if self.provider == WhisperProvider.API
                else WhisperProvider.API
            )

        logger.info(f"Primary transcription failed, trying fallback: {fallback_provider}")

        # Create temporary transcriber for fallback
        try:
            fallback_transcriber = WhisperTranscriber(
                provider=fallback_provider,
                local_model=self.local_model_name,
                language=self.language,
                temperature=self.temperature,
            )
            return fallback_transcriber.transcribe(audio_data)
        except Exception as e:
            logger.error(f"Fallback transcription failed: {e}")
            return None

    def get_available_models(self) -> list[str]:
        """
        Get list of available models for current provider.

        Returns:
            List of model names
        """
        if self.provider == WhisperProvider.API:
            return ["whisper-1"]
        elif self.provider == WhisperProvider.LOCAL:
            return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        else:
            return []

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about current provider configuration.

        Returns:
            Dictionary with provider details
        """
        info = {
            "provider": self.provider.value,
            "language": self.language,
            "temperature": self.temperature,
        }

        if self.provider == WhisperProvider.API:
            info["model"] = self.model
            info["api_available"] = OPENAI_AVAILABLE
        elif self.provider == WhisperProvider.LOCAL:
            info["model"] = self.local_model_name
            info["local_available"] = WHISPER_LOCAL_AVAILABLE

        return info
