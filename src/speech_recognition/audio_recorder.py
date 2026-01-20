"""
Audio recording module for capturing microphone input.

Supports real-time audio capture with automatic silence detection.
"""

from __future__ import annotations

import io
import logging
import threading
import time
import wave
from typing import Any, Optional

try:
    import numpy as np
    import sounddevice as sd

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sd = None
    np = None

logger = logging.getLogger(__name__)


class AudioRecorder:
    """
    Records audio from the microphone with automatic silence detection.

    Features:
    - Real-time audio capture
    - Automatic silence detection
    - Configurable sample rate and channels
    - Thread-safe recording
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        max_duration: float = 60.0,
    ):
        """
        Initialize the audio recorder.

        Args:
            sample_rate: Audio sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            silence_threshold: RMS threshold for silence detection (default: 0.01)
            silence_duration: Seconds of silence before stopping (default: 1.5)
            max_duration: Maximum recording duration in seconds (default: 60)
        """
        if not AUDIO_AVAILABLE:
            raise ImportError(
                "Audio recording requires sounddevice and numpy. "
                "Install with: poetry install --extras speech"
            )

        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration

        self.is_recording = False
        self.audio_data: list[np.ndarray] = []
        self.lock = threading.Lock()
        self.stream: Optional[Any] = None

        self.last_sound_time = 0.0
        self.start_time = 0.0

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: Any,
        status: Any,
    ) -> None:
        """Callback for audio stream data."""
        if status:
            logger.warning(f"Audio callback status: {status}")

        # Calculate RMS (root mean square) for volume detection
        rms = np.sqrt(np.mean(indata**2))

        with self.lock:
            if not self.is_recording:
                return

            # Store audio data
            self.audio_data.append(indata.copy())

            # Update last sound time if above threshold
            if rms > self.silence_threshold:
                self.last_sound_time = time.time()

            # Check for silence timeout or max duration
            elapsed = time.time() - self.start_time
            silence_time = time.time() - self.last_sound_time

            if silence_time > self.silence_duration or elapsed > self.max_duration:
                logger.info(
                    f"Stopping recording: "
                    f"silence={silence_time:.1f}s, duration={elapsed:.1f}s"
                )
                self.is_recording = False

    def start_recording(self) -> None:
        """Start recording audio from the microphone."""
        if self.is_recording:
            logger.warning("Recording already in progress")
            return

        with self.lock:
            self.audio_data = []
            self.is_recording = True
            self.start_time = time.time()
            self.last_sound_time = time.time()

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                dtype=np.float32,
            )
            self.stream.start()
            logger.info("Audio recording started")
        except Exception as e:
            logger.error(f"Failed to start audio recording: {e}")
            self.is_recording = False
            raise

    def stop_recording(self) -> Optional[bytes]:
        """
        Stop recording and return the audio data as WAV bytes.

        Returns:
            WAV format audio bytes, or None if no audio was recorded
        """
        with self.lock:
            self.is_recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if not self.audio_data:
            logger.warning("No audio data recorded")
            return None

        # Concatenate all audio chunks
        audio_array = np.concatenate(self.audio_data, axis=0)

        # Convert to 16-bit PCM
        audio_int16 = (audio_array * 32767).astype(np.int16)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        wav_bytes = wav_buffer.getvalue()
        logger.info(f"Recording stopped, captured {len(wav_bytes)} bytes")

        return wav_bytes

    def is_active(self) -> bool:
        """Check if recording is currently active."""
        with self.lock:
            return self.is_recording

    def get_duration(self) -> float:
        """Get the current recording duration in seconds."""
        if not self.is_recording:
            return 0.0
        return time.time() - self.start_time

    def get_devices(self) -> list[dict[str, Any]]:
        """
        Get list of available audio input devices.

        Returns:
            List of device info dictionaries
        """
        if not AUDIO_AVAILABLE:
            return []

        devices = []
        for idx, device in enumerate(sd.query_devices()):
            if device["max_input_channels"] > 0:
                devices.append(
                    {
                        "index": idx,
                        "name": device["name"],
                        "channels": device["max_input_channels"],
                        "sample_rate": device["default_samplerate"],
                    }
                )

        return devices
