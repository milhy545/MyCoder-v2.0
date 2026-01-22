"""
Azure STT Provider.
"""

import logging
import os
import tempfile
from typing import Any, Dict, Optional

from .base import BaseSTTProvider

logger = logging.getLogger(__name__)

try:
    import azure.cognitiveservices.speech as speechsdk

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class AzureSTTProvider(BaseSTTProvider):
    """Azure Speech-to-Text Provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("AZURE_SPEECH_KEY")
        self.region = config.get("region") or os.getenv("AZURE_SPEECH_REGION")

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        if not AZURE_AVAILABLE or not self.api_key or not self.region:
            logger.error("Azure Speech not available")
            return None

        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.api_key, region=self.region
            )
            speech_config.speech_recognition_language = self.language

            # Use temporary file for input
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                audio_config = speechsdk.audio.AudioConfig(filename=tmp_path)
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config, audio_config=audio_config
                )

                # RecognizeOnceAsync is simpler for short audio
                # Note: This is blocking in this synchronous method wrapper, but thread-safe
                result = recognizer.recognize_once_async().get()
                result_text = None

                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    result_text = result.text
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    logger.warning("Azure: No speech recognized")
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation = result.cancellation_details
                    logger.error(f"Azure canceled: {cancellation.reason}")

                return result_text

            finally:
                try:
                    os.unlink(tmp_path)
                except Exception as exc:
                    logger.debug(
                        "Failed to remove temp audio file %s: %s", tmp_path, exc
                    )

        except Exception as e:
            logger.error(f"Azure STT failed: {e}")
            return None
