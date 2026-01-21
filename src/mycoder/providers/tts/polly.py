"""
Amazon Polly TTS Provider.
"""

import logging
import os
import tempfile
import subprocess
import asyncio
from typing import List, Dict, Any
from contextlib import closing

from .base import BaseTTSProvider

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class AmazonPollyProvider(BaseTTSProvider):
    """Amazon Polly TTS Provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.region_name = config.get("region", "us-east-1")
        # Standard voice ID
        self.voice_id = config.get("voice_id", "Joanna")
        self.engine = config.get("engine", "neural") # or standard

        self.polly = None
        if BOTO3_AVAILABLE:
            try:
                self.polly = boto3.client(
                    "polly",
                    region_name=self.region_name,
                    aws_access_key_id=config.get("aws_access_key_id"),
                    aws_secret_access_key=config.get("aws_secret_access_key")
                )
            except Exception as e:
                logger.error(f"Failed to init Polly: {e}")

    async def speak(self, text: str) -> None:
        if not BOTO3_AVAILABLE or not self.polly:
            logger.error("Polly not available")
            return

        def _synthesize():
            try:
                response = self.polly.synthesize_speech(
                    Text=text,
                    OutputFormat="mp3",
                    VoiceId=self.voice_id,
                    Engine=self.engine
                )

                if "AudioStream" in response:
                    with closing(response["AudioStream"]) as stream:
                        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                            tmp.write(stream.read())
                            return tmp.name
            except (BotoCoreError, ClientError) as error:
                logger.error(f"Polly error: {error}")
                return None
            return None

        tmp_path = await asyncio.to_thread(_synthesize)

        if tmp_path:
            player = self._get_audio_player()
            if player:
                subprocess.run(player + [tmp_path])

            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def stop(self) -> None:
        # Cannot stop boto3 stream easily once downloaded and playing via subprocess unless we track process
        # For now, simplistic implementation
        pass

    def get_available_voices(self) -> List[str]:
        return ["Joanna", "Matthew", "Jitka"] # Jitka is Czech standard

    def _get_audio_player(self) -> List[str]:
        import shutil
        if shutil.which("mpg123"):
            return ["mpg123", "-q"]
        if shutil.which("ffplay"):
            return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
        if shutil.which("afplay"):
            return ["afplay"]
        return None
