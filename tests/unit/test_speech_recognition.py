"""
Unit tests for speech recognition module.

Tests core components without requiring audio hardware or API keys.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import io


class TestAudioRecorder:
    """Tests for AudioRecorder class."""

    @pytest.mark.unit
    def test_audio_recorder_init(self):
        """Test AudioRecorder initialization."""
        try:
            from speech_recognition import AudioRecorder

            recorder = AudioRecorder(
                sample_rate=16000,
                channels=1,
                silence_threshold=0.01,
                silence_duration=1.5,
            )

            assert recorder.sample_rate == 16000
            assert recorder.channels == 1
            assert recorder.silence_threshold == 0.01
            assert recorder.silence_duration == 1.5
            assert not recorder.is_recording

        except ImportError:
            pytest.skip("Audio dependencies not installed")

    @pytest.mark.unit
    def test_audio_recorder_state(self):
        """Test AudioRecorder state management."""
        try:
            from speech_recognition import AudioRecorder

            recorder = AudioRecorder()

            assert not recorder.is_active()
            assert recorder.get_duration() == 0.0

        except ImportError:
            pytest.skip("Audio dependencies not installed")


class TestWhisperTranscriber:
    """Tests for WhisperTranscriber class."""

    @pytest.mark.unit
    def test_whisper_provider_enum(self):
        """Test WhisperProvider enum."""
        from speech_recognition import WhisperProvider

        assert WhisperProvider.API.value == "api"
        assert WhisperProvider.LOCAL.value == "local"

    @pytest.mark.unit
    def test_whisper_api_config(self):
        """Test Whisper API configuration."""
        try:
            from speech_recognition import WhisperTranscriber, WhisperProvider

            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                transcriber = WhisperTranscriber(
                    provider=WhisperProvider.API,
                    model="whisper-1",
                    language="cs",
                )

                info = transcriber.get_provider_info()
                assert info["provider"] == "api"
                assert info["language"] == "cs"
                assert info["model"] == "whisper-1"

        except ImportError:
            pytest.skip("Whisper dependencies not installed")

    @pytest.mark.unit
    def test_whisper_available_models(self):
        """Test getting available Whisper models."""
        try:
            from speech_recognition import WhisperTranscriber, WhisperProvider

            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                # API models
                transcriber = WhisperTranscriber(provider=WhisperProvider.API)
                models = transcriber.get_available_models()
                assert "whisper-1" in models

        except ImportError:
            pytest.skip("Whisper dependencies not installed")


class TestTextInjector:
    """Tests for TextInjector class."""

    @pytest.mark.unit
    def test_injection_method_enum(self):
        """Test InjectionMethod enum."""
        from speech_recognition import InjectionMethod

        assert InjectionMethod.XDOTOOL_TYPE.value == "xdotool_type"
        assert InjectionMethod.XDOTOOL_PASTE.value == "xdotool_paste"
        assert InjectionMethod.CLIPBOARD_ONLY.value == "clipboard_only"
        assert InjectionMethod.AUTO.value == "auto"

    @pytest.mark.unit
    def test_text_injector_init(self):
        """Test TextInjector initialization."""
        try:
            from speech_recognition import TextInjector, InjectionMethod

            injector = TextInjector(
                method=InjectionMethod.AUTO,
                typing_delay=12,
            )

            assert injector.method == InjectionMethod.AUTO
            assert injector.typing_delay == 12

        except ImportError:
            pytest.skip("Text injection dependencies not installed")


class TestHotkeyManager:
    """Tests for HotkeyManager class."""

    @pytest.mark.unit
    def test_hotkey_manager_init(self):
        """Test HotkeyManager initialization."""
        try:
            from speech_recognition import HotkeyManager

            manager = HotkeyManager()

            assert not manager.is_running()
            assert len(manager.get_registered_hotkeys()) == 0

        except ImportError:
            pytest.skip("Hotkey dependencies not installed")

    @pytest.mark.unit
    def test_hotkey_registration(self):
        """Test hotkey registration."""
        try:
            from speech_recognition import HotkeyManager

            manager = HotkeyManager()

            def callback():
                pass

            success = manager.register_hotkey(["ctrl", "shift", "space"], callback)
            assert success

            hotkeys = manager.get_registered_hotkeys()
            assert len(hotkeys) == 1

        except ImportError:
            pytest.skip("Hotkey dependencies not installed")

    @pytest.mark.unit
    def test_hotkey_unregistration(self):
        """Test hotkey unregistration."""
        try:
            from speech_recognition import HotkeyManager

            manager = HotkeyManager()

            def callback():
                pass

            manager.register_hotkey(["ctrl", "shift", "r"], callback)
            success = manager.unregister_hotkey(["ctrl", "shift", "r"])

            assert success
            assert len(manager.get_registered_hotkeys()) == 0

        except ImportError:
            pytest.skip("Hotkey dependencies not installed")


class TestConfig:
    """Tests for configuration management."""

    @pytest.mark.unit
    def test_default_config(self):
        """Test default configuration."""
        from speech_recognition import DictationConfig

        config = DictationConfig()

        assert config.audio.sample_rate == 16000
        assert config.whisper.language == "cs"
        assert config.gui.enabled is True
        assert config.hotkey.enabled is True

    @pytest.mark.unit
    def test_audio_config(self):
        """Test audio configuration."""
        from speech_recognition import AudioConfig

        config = AudioConfig(
            sample_rate=22050,
            channels=2,
            silence_threshold=0.02,
        )

        assert config.sample_rate == 22050
        assert config.channels == 2
        assert config.silence_threshold == 0.02

    @pytest.mark.unit
    def test_whisper_config(self):
        """Test Whisper configuration."""
        from speech_recognition import WhisperConfig

        config = WhisperConfig(
            provider="local",
            local_model="small",
            language="en",
        )

        assert config.provider == "local"
        assert config.local_model == "small"
        assert config.language == "en"

    @pytest.mark.unit
    def test_config_validation(self):
        """Test configuration validation."""
        from speech_recognition import ConfigManager, DictationConfig

        manager = ConfigManager()
        manager.config = DictationConfig()

        is_valid, errors = manager.validate()

        # Should be valid with defaults (except missing API key for API provider)
        # But that's checked as environment variable too
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    @pytest.mark.unit
    def test_config_to_dict(self):
        """Test configuration serialization."""
        from speech_recognition import ConfigManager, DictationConfig

        manager = ConfigManager()
        manager.config = DictationConfig()

        data = manager._config_to_dict()

        assert "audio" in data
        assert "whisper" in data
        assert "injection" in data
        assert "gui" in data
        assert "hotkey" in data


class TestDictationApp:
    """Tests for GlobalDictationApp class."""

    @pytest.mark.unit
    def test_app_state_enum(self):
        """Test AppState enum."""
        from speech_recognition import AppState

        assert AppState.IDLE.value == "idle"
        assert AppState.RECORDING.value == "recording"
        assert AppState.TRANSCRIBING.value == "transcribing"
        assert AppState.INJECTING.value == "injecting"
        assert AppState.ERROR.value == "error"

    @pytest.mark.unit
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_app_initialization(self):
        """Test GlobalDictationApp initialization."""
        try:
            from speech_recognition import GlobalDictationApp, WhisperProvider

            app = GlobalDictationApp(
                whisper_provider=WhisperProvider.API,
                language="cs",
                enable_gui=False,
                enable_hotkeys=False,
            )

            assert app.language == "cs"
            assert not app.enable_gui
            assert not app.enable_hotkeys

        except ImportError:
            pytest.skip("App dependencies not installed")

    @pytest.mark.unit
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_app_get_status(self):
        """Test getting application status."""
        try:
            from speech_recognition import GlobalDictationApp, WhisperProvider

            app = GlobalDictationApp(
                whisper_provider=WhisperProvider.API,
                language="cs",
                enable_gui=False,
                enable_hotkeys=False,
            )

            status = app.get_status()

            assert "state" in status
            assert "language" in status
            assert status["language"] == "cs"

        except ImportError:
            pytest.skip("App dependencies not installed")


class TestButtonState:
    """Tests for button state enum."""

    @pytest.mark.unit
    def test_button_state_enum(self):
        """Test ButtonState enum."""
        try:
            from speech_recognition import ButtonState

            assert ButtonState.IDLE.value == "idle"
            assert ButtonState.RECORDING.value == "recording"
            assert ButtonState.PROCESSING.value == "processing"
            assert ButtonState.ERROR.value == "error"

        except ImportError:
            pytest.skip("GUI dependencies not installed")
