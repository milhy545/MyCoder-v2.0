"""
Speech recognition module for global dictation support.

This module provides components for capturing audio, transcribing speech,
and injecting text into any Linux application.
"""

from .audio_recorder import AudioRecorder
from .whisper_transcriber import WhisperTranscriber, WhisperProvider
from .text_injector import TextInjector, InjectionMethod
from .overlay_button import OverlayButton, OverlayApp, ButtonState
from .hotkey_manager import HotkeyManager
from .dictation_app import GlobalDictationApp, AppState
from .config import (
    ConfigManager,
    DictationConfig,
    AudioConfig,
    WhisperConfig,
    InjectionConfig,
    GuiConfig,
    HotkeyConfig,
    setup_logging,
)

__version__ = "1.0.0"
__all__ = [
    # Core components
    "AudioRecorder",
    "WhisperTranscriber",
    "WhisperProvider",
    "TextInjector",
    "InjectionMethod",
    "OverlayButton",
    "OverlayApp",
    "ButtonState",
    "HotkeyManager",
    "GlobalDictationApp",
    "AppState",
    # Configuration
    "ConfigManager",
    "DictationConfig",
    "AudioConfig",
    "WhisperConfig",
    "InjectionConfig",
    "GuiConfig",
    "HotkeyConfig",
    "setup_logging",
]
