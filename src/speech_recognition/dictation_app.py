"""
Main global dictation application.

Orchestrates audio recording, transcription, and text injection.
"""

import logging
import threading
import time
from typing import Optional, Dict, Any
from enum import Enum

from .audio_recorder import AudioRecorder
from .whisper_transcriber import WhisperTranscriber, WhisperProvider
from .text_injector import TextInjector, InjectionMethod
from .overlay_button import OverlayApp, ButtonState
from .hotkey_manager import HotkeyManager

logger = logging.getLogger(__name__)


class AppState(Enum):
    """Application states."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    INJECTING = "injecting"
    ERROR = "error"


class GlobalDictationApp:
    """
    Global dictation application for Linux.

    Provides system-wide speech-to-text with GUI overlay and hotkeys.
    """

    def __init__(
        self,
        whisper_provider: WhisperProvider = WhisperProvider.API,
        whisper_api_key: Optional[str] = None,
        whisper_model: str = "base",
        language: str = "cs",
        sample_rate: int = 16000,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        injection_method: InjectionMethod = InjectionMethod.AUTO,
        enable_gui: bool = True,
        enable_hotkeys: bool = True,
        hotkey_combo: Optional[list[str]] = None,
    ):
        """
        Initialize the global dictation application.

        Args:
            whisper_provider: Whisper provider (API or LOCAL)
            whisper_api_key: OpenAI API key for Whisper API
            whisper_model: Whisper model name
            language: Language code for transcription (default: "cs")
            sample_rate: Audio sample rate in Hz
            silence_threshold: RMS threshold for silence detection
            silence_duration: Seconds of silence before stopping
            injection_method: Text injection method
            enable_gui: Whether to show GUI overlay
            enable_hotkeys: Whether to enable global hotkeys
            hotkey_combo: Hotkey combination (default: ["ctrl", "shift", "space"])
        """
        self.state = AppState.IDLE
        self.language = language
        self.enable_gui = enable_gui
        self.enable_hotkeys = enable_hotkeys

        # Initialize components
        logger.info("Initializing Global Dictation App...")

        try:
            # Audio recorder
            self.recorder = AudioRecorder(
                sample_rate=sample_rate,
                silence_threshold=silence_threshold,
                silence_duration=silence_duration,
            )
            logger.info("Audio recorder initialized")

            # Whisper transcriber
            self.transcriber = WhisperTranscriber(
                provider=whisper_provider,
                api_key=whisper_api_key,
                local_model=whisper_model,
                language=language,
            )
            logger.info(f"Whisper transcriber initialized: {whisper_provider.value}")

            # Text injector
            self.injector = TextInjector(method=injection_method)
            logger.info("Text injector initialized")

            # GUI overlay (optional)
            self.overlay: Optional[OverlayApp] = None
            if enable_gui:
                self.overlay = OverlayApp(on_click=self.toggle_recording)
                logger.info("GUI overlay initialized")

            # Hotkey manager (optional)
            self.hotkey_manager: Optional[HotkeyManager] = None
            if enable_hotkeys:
                self.hotkey_manager = HotkeyManager()

                # Register default hotkey
                hotkey = hotkey_combo or ["ctrl", "shift", "space"]
                self.hotkey_manager.register_hotkey(hotkey, self.toggle_recording)

                logger.info(f"Hotkey manager initialized with: {'+'.join(hotkey)}")

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise

        # Thread for async operations
        self.processing_thread: Optional[threading.Thread] = None

        logger.info("Global Dictation App ready")

    def toggle_recording(self) -> None:
        """Toggle recording on/off."""
        if self.state == AppState.IDLE:
            self.start_recording()
        elif self.state == AppState.RECORDING:
            self.stop_recording()
        else:
            logger.warning(f"Cannot toggle recording in state: {self.state.value}")

    def start_recording(self) -> None:
        """Start recording audio."""
        if self.state != AppState.IDLE:
            logger.warning(f"Cannot start recording in state: {self.state.value}")
            return

        try:
            logger.info("Starting recording...")
            self.state = AppState.RECORDING

            # Update GUI
            if self.overlay:
                self.overlay.button.set_state(ButtonState.RECORDING)

            # Start recording
            self.recorder.start_recording()

            logger.info("Recording started - speak now")

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self._handle_error("Failed to start recording")

    def stop_recording(self) -> None:
        """Stop recording and process audio."""
        if self.state != AppState.RECORDING:
            logger.warning(f"Cannot stop recording in state: {self.state.value}")
            return

        try:
            logger.info("Stopping recording...")

            # Stop recording and get audio data
            audio_data = self.recorder.stop_recording()

            if not audio_data:
                logger.warning("No audio data recorded")
                self._handle_error("No audio recorded")
                return

            # Process audio in separate thread
            self.processing_thread = threading.Thread(
                target=self._process_audio,
                args=(audio_data,),
                daemon=True,
            )
            self.processing_thread.start()

        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            self._handle_error("Failed to stop recording")

    def _process_audio(self, audio_data: bytes) -> None:
        """
        Process recorded audio (transcribe and inject).

        Args:
            audio_data: Audio data in WAV format
        """
        try:
            # Transcribe
            self.state = AppState.TRANSCRIBING

            if self.overlay:
                self.overlay.button.set_state(ButtonState.PROCESSING)
                self.overlay.button.set_status("Transcribing...")

            logger.info("Transcribing audio...")
            text = self.transcriber.transcribe(audio_data)

            if not text:
                logger.warning("Transcription returned no text")
                self._handle_error("No text recognized")
                return

            logger.info(f"Transcribed: {text[:100]}...")

            # Inject text
            self.state = AppState.INJECTING

            if self.overlay:
                self.overlay.button.set_status("Injecting text...")

            logger.info("Injecting text into active window...")

            # Small delay to allow user to focus target window
            time.sleep(0.3)

            success = self.injector.inject_text(text)

            if success:
                logger.info("Text injected successfully")

                if self.overlay:
                    self.overlay.button.show_notification("✓ Done!", duration=1500)

            else:
                logger.error("Failed to inject text")
                self._handle_error("Failed to inject text")
                return

            # Return to idle state
            self.state = AppState.IDLE

            if self.overlay:
                self.overlay.button.set_state(ButtonState.IDLE)

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            self._handle_error(f"Processing error: {str(e)[:50]}")

    def _handle_error(self, message: str) -> None:
        """
        Handle application error.

        Args:
            message: Error message
        """
        logger.error(f"Application error: {message}")

        self.state = AppState.ERROR

        if self.overlay:
            self.overlay.button.flash_error()
            self.overlay.button.set_status(message)

        # Reset to idle after delay
        def reset():
            time.sleep(2)
            self.state = AppState.IDLE
            if self.overlay:
                self.overlay.button.set_state(ButtonState.IDLE)

        threading.Thread(target=reset, daemon=True).start()

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Exit code
        """
        try:
            logger.info("Starting Global Dictation App...")

            # Start hotkey listener
            if self.hotkey_manager:
                self.hotkey_manager.start()
                logger.info("Hotkey listener started")

            # Show GUI and run event loop
            if self.overlay:
                logger.info("Starting GUI...")
                return self.overlay.run()
            else:
                # Run without GUI (hotkey only mode)
                logger.info("Running in hotkey-only mode (no GUI)")
                logger.info("Press Ctrl+C to exit")

                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Shutting down...")
                    return 0

        except Exception as e:
            logger.error(f"Application error: {e}")
            return 1

        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown the application cleanly."""
        logger.info("Shutting down Global Dictation App...")

        # Stop recording if active
        if self.state == AppState.RECORDING:
            self.recorder.stop_recording()

        # Stop hotkey listener
        if self.hotkey_manager:
            self.hotkey_manager.stop()

        # Hide GUI
        if self.overlay:
            self.overlay.hide()

        logger.info("Shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """
        Get application status information.

        Returns:
            Dictionary with status details
        """
        status = {
            "state": self.state.value,
            "language": self.language,
            "gui_enabled": self.enable_gui,
            "hotkeys_enabled": self.enable_hotkeys,
            "transcriber": self.transcriber.get_provider_info(),
        }

        if self.hotkey_manager:
            status["registered_hotkeys"] = self.hotkey_manager.get_registered_hotkeys()

        if self.recorder:
            status["recording_active"] = self.recorder.is_active()
            status["recording_duration"] = self.recorder.get_duration()

        return status

    def test_components(self) -> Dict[str, bool]:
        """
        Test all application components.

        Returns:
            Dictionary with test results
        """
        results = {}

        # Test audio devices
        try:
            devices = self.recorder.get_devices()
            results["audio_devices"] = len(devices) > 0
            logger.info(f"Found {len(devices)} audio input devices")
        except Exception as e:
            logger.error(f"Audio device test failed: {e}")
            results["audio_devices"] = False

        # Test text injection
        try:
            window_info = self.injector.get_active_window_info()
            results["window_detection"] = window_info is not None
            if window_info:
                logger.info(f"Active window: {window_info['name']}")
        except Exception as e:
            logger.error(f"Window detection test failed: {e}")
            results["window_detection"] = False

        # Test transcriber
        try:
            info = self.transcriber.get_provider_info()
            results["transcriber"] = True
            logger.info(f"Transcriber: {info['provider']}")
        except Exception as e:
            logger.error(f"Transcriber test failed: {e}")
            results["transcriber"] = False

        return results
