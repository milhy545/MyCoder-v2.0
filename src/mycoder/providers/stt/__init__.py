"""
STT Providers Module.
"""

from .azure import AzureSTTProvider
from .base import BaseSTTProvider
from .deepl import DeepLSTTProvider
from .google import GoogleSTTProvider
from .whisper import WhisperProviderType, WhisperSTTProvider

__all__ = [
    "BaseSTTProvider",
    "WhisperSTTProvider",
    "WhisperProviderType",
    "GoogleSTTProvider",
    "AzureSTTProvider",
    "DeepLSTTProvider",
]
