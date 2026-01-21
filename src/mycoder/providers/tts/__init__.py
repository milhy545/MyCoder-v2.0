"""
TTS Providers Module.
"""

from .azure import AzureTTSProvider
from .base import BaseTTSProvider
from .elevenlabs import ElevenLabsProvider
from .gtts_provider import GTTSProvider
from .local import EspeakProvider, Pyttsx3Provider
from .polly import AmazonPollyProvider

__all__ = [
    "BaseTTSProvider",
    "Pyttsx3Provider",
    "EspeakProvider",
    "GTTSProvider",
    "AzureTTSProvider",
    "AmazonPollyProvider",
    "ElevenLabsProvider",
]
