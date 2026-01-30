"""
ElevenLabs TTS Provider.
"""

import json
import logging
import os
import subprocess
import tempfile
import urllib.request
from typing import Any, Dict, List, Optional

import aiohttp

from .base import BaseTTSProvider

logger = logging.getLogger(__name__)


class ElevenLabsProvider(BaseTTSProvider):
    """ElevenLabs TTS Provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("ELEVENLABS_API_KEY")
        self.model = config.get("model", "eleven_monolingual_v1")
        # Default to a standard voice ID if none provided
        self.voice_id = config.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Rachel
        self._current_process = None
        self._voices_cache: Optional[List[str]] = None

    async def speak(self, text: str) -> None:
        if not self.api_key:
            logger.error("ElevenLabs API key not found")
            return

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        data = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"ElevenLabs error {response.status}: {error_text}"
                        )
                        return

                    # Stream to temp file and play
                    with tempfile.NamedTemporaryFile(
                        suffix=".mp3", delete=False
                    ) as tmp:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            tmp.write(chunk)
                        tmp_path = tmp.name

            # Play audio (using simple player detection from original engine)
            # This logic should ideally be shared but I'll replicate for now
            player = self._get_audio_player()
            if player:
                self._current_process = subprocess.Popen(player + [tmp_path])
                self._current_process.wait()

            try:
                os.unlink(tmp_path)
            except Exception as exc:
                logger.debug("Failed to remove temp audio file %s: %s", tmp_path, exc)

        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")

    def stop(self) -> None:
        if self._current_process:
            self._current_process.terminate()
            self._current_process = None

    def get_available_voices(self) -> List[str]:
        """
        Fetch available voices from ElevenLabs API.
        Returns a list of strings formatted as "Name (voice_id)".
        Uses internal caching to avoid redundant API calls.
        """
        if self._voices_cache is not None:
            return self._voices_cache

        if not self.api_key:
            logger.error("ElevenLabs API key not found, cannot list voices")
            return []

        url = "https://api.elevenlabs.io/v1/voices"
        req = urllib.request.Request(url)
        req.add_header("xi-api-key", self.api_key)
        req.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    logger.error(
                        f"ElevenLabs voices API failed with status {response.status}"
                    )
                    return []

                data = json.loads(response.read().decode("utf-8"))
                voices_data = data.get("voices", [])

                # Format: "Name (voice_id)"
                formatted_voices = []
                for v in voices_data:
                    name = v.get("name", "Unknown")
                    voice_id = v.get("voice_id", "Unknown")
                    formatted_voices.append(f"{name} ({voice_id})")

                self._voices_cache = formatted_voices
                return formatted_voices

        except Exception as e:
            logger.error(f"Failed to fetch ElevenLabs voices: {e}")
            return []

    def _get_audio_player(self) -> List[str]:
        import shutil

        if shutil.which("mpg123"):
            return ["mpg123", "-q"]
        if shutil.which("ffplay"):
            return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
        if shutil.which("afplay"):
            return ["afplay"]
        return None
