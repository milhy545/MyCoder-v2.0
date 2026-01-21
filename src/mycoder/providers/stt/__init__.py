"""
STT Providers Module.
"""

from .base import BaseSTTProvider
from .whisper import WhisperSTTProvider, WhisperProviderType
from .google import GoogleSTTProvider
from .azure import AzureSTTProvider
from .deepl import DeepLSTTProvider

__all__ = [
    "BaseSTTProvider",
    "WhisperSTTProvider",
    "WhisperProviderType",
    "GoogleSTTProvider",
    "AzureSTTProvider",
    "DeepLSTTProvider",
]
