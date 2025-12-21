"""
Configuration management for global dictation application.

Handles loading, saving, and validating configuration settings.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio recording configuration."""

    sample_rate: int = 16000
    channels: int = 1
    silence_threshold: float = 0.01
    silence_duration: float = 1.5
    max_duration: float = 60.0


@dataclass
class WhisperConfig:
    """Whisper transcription configuration."""

    provider: str = "api"  # "api" or "local"
    api_key: Optional[str] = None
    model: str = "whisper-1"  # For API
    local_model: str = "base"  # For local (tiny, base, small, medium, large)
    language: str = "cs"
    temperature: float = 0.0


@dataclass
class InjectionConfig:
    """Text injection configuration."""

    method: str = "auto"  # "xdotool_type", "xdotool_paste", "clipboard_only", "auto"
    typing_delay: int = 12
    use_clipboard_backup: bool = True


@dataclass
class GuiConfig:
    """GUI overlay configuration."""

    enabled: bool = True
    button_size: int = 80
    position_x: Optional[int] = None
    position_y: Optional[int] = None


@dataclass
class HotkeyConfig:
    """Global hotkey configuration."""

    enabled: bool = True
    combination: list[str] = field(default_factory=lambda: ["ctrl", "shift", "space"])


@dataclass
class DictationConfig:
    """Complete dictation application configuration."""

    audio: AudioConfig = field(default_factory=AudioConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    injection: InjectionConfig = field(default_factory=InjectionConfig)
    gui: GuiConfig = field(default_factory=GuiConfig)
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None


class ConfigManager:
    """
    Manages application configuration.

    Handles loading from file, environment variables, and defaults.
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "mycoder" / "dictation_config.json"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file (default: ~/.config/mycoder/dictation_config.json)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = DictationConfig()

    def load(self) -> DictationConfig:
        """
        Load configuration from file and environment variables.

        Returns:
            Loaded configuration
        """
        # Start with defaults
        self.config = DictationConfig()

        # Load from file if exists
        if self.config_path.exists():
            try:
                self._load_from_file()
                logger.info(f"Loaded configuration from: {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                logger.info("Using default configuration")

        # Override with environment variables
        self._load_from_env()

        return self.config

    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        with open(self.config_path, "r") as f:
            data = json.load(f)

        # Audio config
        if "audio" in data:
            self.config.audio = AudioConfig(**data["audio"])

        # Whisper config
        if "whisper" in data:
            self.config.whisper = WhisperConfig(**data["whisper"])

        # Injection config
        if "injection" in data:
            self.config.injection = InjectionConfig(**data["injection"])

        # GUI config
        if "gui" in data:
            self.config.gui = GuiConfig(**data["gui"])

        # Hotkey config
        if "hotkey" in data:
            self.config.hotkey = HotkeyConfig(**data["hotkey"])

        # Logging config
        if "log_level" in data:
            self.config.log_level = data["log_level"]
        if "log_file" in data:
            self.config.log_file = data["log_file"]

    def _load_from_env(self) -> None:
        """Override configuration with environment variables."""
        # Whisper API key
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.config.whisper.api_key = api_key

        # Whisper provider
        provider = os.getenv("DICTATION_WHISPER_PROVIDER")
        if provider:
            self.config.whisper.provider = provider

        # Language
        language = os.getenv("DICTATION_LANGUAGE")
        if language:
            self.config.whisper.language = language

        # Log level
        log_level = os.getenv("DICTATION_LOG_LEVEL")
        if log_level:
            self.config.log_level = log_level

        # GUI enabled
        gui_enabled = os.getenv("DICTATION_GUI_ENABLED")
        if gui_enabled:
            self.config.gui.enabled = gui_enabled.lower() in ("true", "1", "yes")

        # Hotkey enabled
        hotkey_enabled = os.getenv("DICTATION_HOTKEY_ENABLED")
        if hotkey_enabled:
            self.config.hotkey.enabled = hotkey_enabled.lower() in ("true", "1", "yes")

    def save(self) -> bool:
        """
        Save current configuration to file.

        Returns:
            True if save was successful
        """
        try:
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert config to dict
            data = self._config_to_dict()

            # Write to file
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved configuration to: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "audio": asdict(self.config.audio),
            "whisper": {
                **asdict(self.config.whisper),
                # Don't save API key to file
                "api_key": None,
            },
            "injection": asdict(self.config.injection),
            "gui": asdict(self.config.gui),
            "hotkey": asdict(self.config.hotkey),
            "log_level": self.config.log_level,
            "log_file": self.config.log_file,
        }

    def create_default_config(self) -> bool:
        """
        Create default configuration file.

        Returns:
            True if creation was successful
        """
        self.config = DictationConfig()
        return self.save()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate current configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Validate audio config
        if self.config.audio.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            errors.append(
                f"Invalid sample rate: {self.config.audio.sample_rate}. "
                "Must be one of: 8000, 16000, 22050, 44100, 48000"
            )

        if (
            self.config.audio.silence_threshold < 0
            or self.config.audio.silence_threshold > 1
        ):
            errors.append(
                f"Invalid silence threshold: {self.config.audio.silence_threshold}. "
                "Must be between 0 and 1"
            )

        # Validate whisper config
        if self.config.whisper.provider not in ["api", "local"]:
            errors.append(
                f"Invalid Whisper provider: {self.config.whisper.provider}. "
                "Must be 'api' or 'local'"
            )

        if self.config.whisper.provider == "api" and not self.config.whisper.api_key:
            # Check environment variable as fallback
            if not os.getenv("OPENAI_API_KEY"):
                errors.append(
                    "Whisper API provider requires api_key. "
                    "Set in config or OPENAI_API_KEY environment variable"
                )

        # Validate injection config
        valid_methods = ["xdotool_type", "xdotool_paste", "clipboard_only", "auto"]
        if self.config.injection.method not in valid_methods:
            errors.append(
                f"Invalid injection method: {self.config.injection.method}. "
                f"Must be one of: {', '.join(valid_methods)}"
            )

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.config.log_level.upper() not in valid_log_levels:
            errors.append(
                f"Invalid log level: {self.config.log_level}. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )

        return len(errors) == 0, errors

    def get_summary(self) -> str:
        """
        Get human-readable configuration summary.

        Returns:
            Configuration summary string
        """
        lines = [
            "=== Global Dictation Configuration ===",
            "",
            "Audio:",
            f"  Sample Rate: {self.config.audio.sample_rate} Hz",
            f"  Silence Duration: {self.config.audio.silence_duration}s",
            "",
            "Whisper:",
            f"  Provider: {self.config.whisper.provider}",
            f"  Model: {self.config.whisper.model if self.config.whisper.provider == 'api' else self.config.whisper.local_model}",
            f"  Language: {self.config.whisper.language}",
            "",
            "Text Injection:",
            f"  Method: {self.config.injection.method}",
            "",
            "GUI:",
            f"  Enabled: {self.config.gui.enabled}",
            f"  Button Size: {self.config.gui.button_size}px",
            "",
            "Hotkey:",
            f"  Enabled: {self.config.hotkey.enabled}",
            f"  Combination: {'+'.join(self.config.hotkey.combination)}",
            "",
            "Logging:",
            f"  Level: {self.config.log_level}",
        ]

        return "\n".join(lines)


def setup_logging(config: DictationConfig) -> None:
    """
    Setup logging based on configuration.

    Args:
        config: Application configuration
    """
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]

    if config.log_file:
        try:
            log_path = Path(config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(config.log_file))
        except Exception as e:
            print(f"Warning: Failed to setup log file: {e}")

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )
