"""
Speech recognition module for global dictation support.

This module provides components for capturing audio, transcribing speech,
and injecting text into any Linux application.
"""

from .audio_recorder import AudioRecorder
from .config import (
    AudioConfig,
    ConfigManager,
    DictationConfig,
    GuiConfig,
    HotkeyConfig,
    InjectionConfig,
    WhisperConfig,
    setup_logging,
)
from .dictation_app import AppState, GlobalDictationApp
from .hotkey_manager import HotkeyManager
from .overlay_button import ButtonState, OverlayApp, OverlayButton
from .text_injector import InjectionMethod, TextInjector
from .whisper_transcriber import WhisperProvider, WhisperTranscriber

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
