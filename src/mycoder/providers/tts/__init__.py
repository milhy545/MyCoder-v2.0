"""
TTS Providers Module.
"""

from .base import BaseTTSProvider
from .local import Pyttsx3Provider, EspeakProvider
from .gtts_provider import GTTSProvider
from .azure import AzureTTSProvider
from .polly import AmazonPollyProvider
from .elevenlabs import ElevenLabsProvider

__all__ = [
    "BaseTTSProvider",
    "Pyttsx3Provider",
    "EspeakProvider",
    "GTTSProvider",
    "AzureTTSProvider",
    "AmazonPollyProvider",
    "ElevenLabsProvider",
]
