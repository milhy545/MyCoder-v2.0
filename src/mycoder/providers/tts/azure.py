"""
Microsoft Azure TTS Provider.
"""

import asyncio
import logging
import os
import tempfile
from typing import Any, Dict, List

from .base import BaseTTSProvider

logger = logging.getLogger(__name__)

try:
    import azure.cognitiveservices.speech as speechsdk

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class AzureTTSProvider(BaseTTSProvider):
    """Microsoft Azure Speech Service Provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("AZURE_SPEECH_KEY")
        self.region = config.get("region") or os.getenv("AZURE_SPEECH_REGION")
        self.voice_name = config.get("voice_name", "en-US-JennyNeural")

        self.synthesizer = None
        if AZURE_AVAILABLE and self.api_key and self.region:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.api_key, region=self.region
            )
            speech_config.speech_synthesis_voice_name = self.voice_name
            # Output to speaker directly by default, or stream if needed
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            self.synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=audio_config
            )

    async def speak(self, text: str) -> None:
        if not AZURE_AVAILABLE:
            logger.error("Azure Speech SDK not installed")
            return
        if not self.synthesizer:
            logger.error("Azure Synthesizer not initialized")
            return

        def _speak():
            result = self.synthesizer.speak_text_async(text).get()
            if result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Azure Speech canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation_details.error_details}")

        await asyncio.to_thread(_speak)

    def stop(self) -> None:
        if self.synthesizer:
            self.synthesizer.stop_speaking_async()

    def get_available_voices(self) -> List[str]:
        return ["en-US-JennyNeural", "cs-CZ-AntoninNeural", "cs-CZ-VlastaNeural"]
