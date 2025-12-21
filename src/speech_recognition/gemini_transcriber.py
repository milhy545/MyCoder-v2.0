"""
Extended Whisper transcriber with Gemini support.

Adds Google Gemini as an alternative API provider.
"""

import logging
import os
from typing import Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

logger = logging.getLogger(__name__)


class GeminiTranscriber:
    """
    Speech transcription using Google Gemini API.

    Free tier available with generous limits.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        language: str = "cs",
    ):
        """
        Initialize Gemini transcriber.

        Args:
            api_key: Google Gemini API key
            model: Gemini model name (default: gemini-1.5-flash)
            language: Language code for transcription (default: "cs")
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "Gemini API requires google-generativeai package. "
                "Install with: pip install google-generativeai"
            )

        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter"
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.language = language

        logger.info(f"Initialized Gemini transcriber with model {model}")

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio using Gemini API.

        Args:
            audio_data: Audio data in WAV format

        Returns:
            Transcribed text, or None if transcription failed
        """
        try:
            # Gemini supports audio input directly
            logger.info("Transcribing audio via Gemini API")

            # Upload audio file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                # Upload to Gemini
                audio_file = genai.upload_file(tmp_path)

                # Create prompt for transcription
                prompt = f"Transcribe this audio to text in {self.language} language. Output only the transcribed text without any additional commentary."

                # Generate response
                response = self.model.generate_content([prompt, audio_file])

                text = response.text.strip()
                logger.info(f"Gemini transcription successful: {len(text)} characters")

                return text

            finally:
                # Cleanup
                import os
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Gemini transcription failed: {e}")
            return None
