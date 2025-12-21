"""
Comprehensive Unit Tests for Configuration Manager

Tests the configuration system with multiple sources,
validation, and integration with multi-API providers.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config_manager import (
    ConfigManager,
    MyCoderConfig,
    APIProviderSettings,
    ThermalSettings,
    SystemSettings,
    get_config_manager,
    load_config,
)


class TestAPIProviderSettings:
    """Test APIProviderSettings data class"""

    def test_default_settings(self):
        """Test default provider settings"""
        settings = APIProviderSettings()

        assert settings.enabled is True
        assert settings.timeout_seconds == 30
        assert settings.max_retries == 3
        assert settings.model is None
        assert settings.base_url is None
        assert settings.api_key is None
        assert settings.priority == 10

    def test_custom_settings(self):
        """Test custom provider settings"""
        settings = APIProviderSettings(
            enabled=False,
            timeout_seconds=60,
            max_retries=5,
            model="claude-3-5-sonnet",
            base_url="https://api.custom.com",
            api_key="test_key",
            priority=1,
        )

        assert settings.enabled is False
        assert settings.timeout_seconds == 60
        assert settings.max_retries == 5
        assert settings.model == "claude-3-5-sonnet"
        assert settings.base_url == "https://api.custom.com"
        assert settings.api_key == "test_key"
        assert settings.priority == 1


class TestThermalSettings:
    """Test ThermalSettings data class"""

    def test_default_thermal_settings(self):
        """Test default thermal settings"""
        settings = ThermalSettings()

        assert settings.enabled is True
        assert settings.max_temp == 80
        assert settings.critical_temp == 85
        assert settings.check_interval == 30
        assert settings.throttle_on_high is True
        assert settings.emergency_shutdown is False
        assert (
            "/PowerManagement/scripts/performance_manager.sh"
            in settings.performance_script
        )

    def test_custom_thermal_settings(self):
        """Test custom thermal settings"""
        settings = ThermalSettings(
            enabled=False,
            max_temp=75,
            critical_temp=82,
            check_interval=60,
            throttle_on_high=False,
            emergency_shutdown=True,
            performance_script="/custom/thermal/script.sh",
        )

        assert settings.enabled is False
        assert settings.max_temp == 75
        assert settings.critical_temp == 82
        assert settings.check_interval == 60
        assert settings.throttle_on_high is False
        assert settings.emergency_shutdown is True
        assert settings.performance_script == "/custom/thermal/script.sh"


class TestSystemSettings:
    """Test SystemSettings data class"""

    def test_default_system_settings(self):
        """Test default system settings"""
        settings = SystemSettings()

        assert settings.working_directory is None
        assert settings.log_level == "INFO"
        assert settings.session_timeout_hours == 24
        assert settings.max_concurrent_requests == 10
        assert settings.enable_tool_registry is True
        assert settings.enable_mcp_integration is True

    def test_custom_system_settings(self):
        """Test custom system settings"""
        settings = SystemSettings(
            working_directory="/custom/work/dir",
            log_level="DEBUG",
            session_timeout_hours=48,
            max_concurrent_requests=20,
            enable_tool_registry=False,
            enable_mcp_integration=False,
        )

        assert settings.working_directory == "/custom/work/dir"
        assert settings.log_level == "DEBUG"
        assert settings.session_timeout_hours == 48
        assert settings.max_concurrent_requests == 20
        assert settings.enable_tool_registry is False
        assert settings.enable_mcp_integration is False


class TestMyCoderConfig:
    """Test MyCoderConfig main configuration class"""

    def create_test_config(self):
        """Create test configuration"""
        return MyCoderConfig(
            claude_anthropic=APIProviderSettings(
                enabled=True, model="claude-3-5-sonnet"
            ),
            claude_oauth=APIProviderSettings(enabled=True, priority=2),
            gemini=APIProviderSettings(enabled=False, model="gemini-1.5-pro"),
            ollama_local=APIProviderSettings(
                enabled=True, base_url="http://localhost:11434"
            ),
            ollama_remote_urls=["http://remote1:11434", "http://remote2:11434"],
            thermal=ThermalSettings(enabled=True, max_temp=78),
            system=SystemSettings(log_level="DEBUG"),
            preferred_provider="claude_anthropic",
            fallback_enabled=True,
            debug_mode=True,
        )

    def test_config_creation(self):
        """Test configuration creation"""
        config = self.create_test_config()

        assert config.claude_anthropic.enabled is True
        assert config.claude_anthropic.model == "claude-3-5-sonnet"
        assert config.claude_oauth.priority == 2
        assert config.gemini.enabled is False
        assert config.ollama_local.base_url == "http://localhost:11434"
        assert len(config.ollama_remote_urls) == 2
        assert config.thermal.max_temp == 78
        assert config.system.log_level == "DEBUG"
        assert config.preferred_provider == "claude_anthropic"
        assert config.fallback_enabled is True
        assert config.debug_mode is True


class TestConfigManager:
    """Test ConfigManager class"""

    def create_manager(self, config_path=None):
        """Create config manager"""
        return ConfigManager(config_path)

    def test_manager_initialization(self):
        """Test manager initialization"""
        manager = self.create_manager()

        assert manager.config_path is None
        assert manager.config is None
        assert manager._env_prefix == "MYCODER_"
        assert len(manager.DEFAULT_CONFIG_LOCATIONS) > 0

    def test_manager_with_custom_path(self):
        """Test manager with custom config path"""
        custom_path = Path("/custom/config.json")
        manager = self.create_manager(custom_path)

        assert manager.config_path == custom_path

    def test_get_default_config(self):
        """Test default configuration generation"""
        manager = self.create_manager()
        defaults = manager._get_default_config()

        assert "claude_anthropic" in defaults
        assert "claude_oauth" in defaults
        assert "gemini" in defaults
        assert "ollama_local" in defaults
        assert "thermal" in defaults
        assert "system" in defaults

        # Test specific defaults
        assert defaults["claude_anthropic"]["enabled"] is True
        assert defaults["claude_anthropic"]["model"] == "claude-3-5-sonnet-20241022"
        assert defaults["claude_anthropic"]["priority"] == 1
        assert defaults["claude_oauth"]["priority"] == 2
        assert defaults["gemini"]["priority"] == 3
        assert defaults["ollama_local"]["priority"] == 4
        assert defaults["thermal"]["max_temp"] == 80
        assert defaults["system"]["log_level"] == "INFO"

    def test_parse_env_value_boolean(self):
        """Test environment value parsing for booleans"""
        manager = self.create_manager()

        assert manager._parse_env_value("true") is True
        assert manager._parse_env_value("True") is True
        assert manager._parse_env_value("TRUE") is True
        assert manager._parse_env_value("false") is False
        assert manager._parse_env_value("False") is False
        assert manager._parse_env_value("FALSE") is False

    def test_parse_env_value_numeric(self):
        """Test environment value parsing for numbers"""
        manager = self.create_manager()

        assert manager._parse_env_value("123") == 123
        assert manager._parse_env_value("45.67") == 45.67
        assert manager._parse_env_value("0") == 0

    def test_parse_env_value_list(self):
        """Test environment value parsing for lists"""
        manager = self.create_manager()

        result = manager._parse_env_value("item1,item2,item3")
        assert result == ["item1", "item2", "item3"]

        result = manager._parse_env_value("single")
        assert result == "single"  # Single item remains string

    def test_parse_env_value_string(self):
        """Test environment value parsing for strings"""
        manager = self.create_manager()

        assert manager._parse_env_value("hello") == "hello"
        assert manager._parse_env_value("hello world") == "hello world"
        assert manager._parse_env_value("") == ""

    def test_merge_deep(self):
        """Test deep dictionary merging"""
        manager = self.create_manager()

        base = {
            "level1": {
                "level2": {"key1": "base_value1", "key2": "base_value2"},
                "key3": "base_value3",
            },
            "key4": "base_value4",
        }

        overlay = {
            "level1": {
                "level2": {
                    "key1": "overlay_value1",  # Override
                    "key_new": "overlay_new",  # Add new
                }
            },
            "key5": "overlay_value5",  # Add new top-level
        }

        result = manager._merge_deep(base, overlay)

        assert result["level1"]["level2"]["key1"] == "overlay_value1"  # Overridden
        assert result["level1"]["level2"]["key2"] == "base_value2"  # Preserved
        assert result["level1"]["level2"]["key_new"] == "overlay_new"  # Added
        assert result["level1"]["key3"] == "base_value3"  # Preserved
        assert result["key4"] == "base_value4"  # Preserved
        assert result["key5"] == "overlay_value5"  # Added

    @patch.dict(
        os.environ,
        {"MYCODER_DEBUG_MODE": "true", "MYCODER_PREFERRED_PROVIDER": "gemini"},
    )
    def test_load_env_config(self):
        """Test loading configuration from environment variables"""
        manager = self.create_manager()
        env_config = manager._load_env_config()

        assert env_config["debug_mode"] is True
        assert env_config["preferred_provider"] == "gemini"

    @patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "test_anthropic_key",
            "GEMINI_API_KEY": "test_gemini_key",
        },
    )
    def test_load_env_config_api_keys(self):
        """Test loading API keys from environment"""
        manager = self.create_manager()
        env_config = manager._load_env_config()

        assert env_config["anthropic"]["api_key"] == "test_anthropic_key"
        assert env_config["gemini"]["api_key"] == "test_gemini_key"

    def test_load_env_file(self):
        """Test loading configuration from environment file"""
        env_content = """
# MyCoder Configuration
MYCODER_DEBUG_MODE=true
MYCODER_THERMAL_MAX_TEMP=75
MYCODER_CLAUDE_ANTHROPIC_ENABLED=false
MYCODER_OLLAMA_REMOTE_URLS=http://server1:11434,http://server2:11434
# Comment line
INVALID_LINE_WITHOUT_EQUALS
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            env_file_path = Path(f.name)

        try:
            manager = self.create_manager()
            config = manager._load_env_file(env_file_path)

            assert config["debug_mode"] is True
            assert config["thermal_max_temp"] == 75
            assert config["claude_anthropic_enabled"] is False
            assert config["ollama_remote_urls"] == [
                "http://server1:11434",
                "http://server2:11434",
            ]

        finally:
            env_file_path.unlink()

    def test_load_file_config_json(self):
        """Test loading configuration from JSON file"""
        config_data = {
            "claude_anthropic": {
                "enabled": True,
                "model": "claude-3-5-sonnet",
                "timeout_seconds": 45,
            },
            "thermal": {"enabled": False, "max_temp": 85},
            "preferred_provider": "claude_anthropic",
            "debug_mode": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            json_file_path = Path(f.name)

        try:
            manager = ConfigManager(json_file_path)
            file_config = manager._load_file_config()

            assert file_config["claude_anthropic"]["enabled"] is True
            assert file_config["claude_anthropic"]["model"] == "claude-3-5-sonnet"
            assert file_config["claude_anthropic"]["timeout_seconds"] == 45
            assert file_config["thermal"]["enabled"] is False
            assert file_config["thermal"]["max_temp"] == 85
            assert file_config["preferred_provider"] == "claude_anthropic"
            assert file_config["debug_mode"] is True

        finally:
            json_file_path.unlink()

    def test_load_file_config_nonexistent(self):
        """Test loading config when file doesn't exist"""
        manager = self.create_manager()
        file_config = manager._load_file_config()

        assert file_config is None

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_load_file_config_permission_error(self, mock_open, mock_exists):
        """Test handling file permission errors"""
        manager = ConfigManager(Path("/restricted/config.json"))
        file_config = manager._load_file_config()

        assert file_config is None

    def test_dict_to_config_success(self):
        """Test converting dictionary to config object"""
        config_dict = {
            "claude_anthropic": {
                "enabled": True,
                "model": "claude-3-5-sonnet",
                "timeout_seconds": 45,
            },
            "claude_oauth": {"enabled": True, "priority": 2},
            "gemini": {"enabled": False, "api_key": "test_key"},
            "ollama_local": {"enabled": True, "base_url": "http://localhost:11434"},
            "ollama_remote_urls": ["http://remote:11434"],
            "thermal": {"enabled": True, "max_temp": 78},
            "system": {"log_level": "DEBUG"},
            "preferred_provider": "claude_anthropic",
            "debug_mode": True,
        }

        manager = self.create_manager()
        config = manager._dict_to_config(config_dict)

        assert isinstance(config, MyCoderConfig)
        assert config.claude_anthropic.enabled is True
        assert config.claude_anthropic.model == "claude-3-5-sonnet"
        assert config.claude_anthropic.timeout_seconds == 45
        assert config.claude_oauth.priority == 2
        assert config.gemini.api_key == "test_key"
        assert config.ollama_local.base_url == "http://localhost:11434"
        assert config.ollama_remote_urls == ["http://remote:11434"]
        assert config.thermal.max_temp == 78
        assert config.system.log_level == "DEBUG"
        assert config.preferred_provider == "claude_anthropic"
        assert config.debug_mode is True

    def test_dict_to_config_missing_required_fields(self):
        """Test config creation with missing required fields"""
        # Empty dict should still work with defaults
        config_dict = {}

        manager = self.create_manager()

        with pytest.raises(ValueError):
            manager._dict_to_config(config_dict)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_validate_config_api_keys(self):
        """Test configuration validation for API keys"""
        manager = self.create_manager()

        # Load minimal config
        config_dict = manager._get_default_config()
        config_dict["claude_anthropic"]["enabled"] = True

        manager.config = manager._dict_to_config(config_dict)

        # Should not raise warnings with API key in environment
        manager._validate_config()  # Should complete without errors

    @patch.dict(os.environ, {}, clear=True)  # Clear environment
    def test_validate_config_missing_api_keys(self):
        """Test validation warnings for missing API keys"""
        manager = self.create_manager()

        config_dict = manager._get_default_config()
        config_dict["claude_anthropic"]["enabled"] = True
        config_dict["gemini"]["enabled"] = True

        manager.config = manager._dict_to_config(config_dict)

        with patch("src.config_manager.logger") as mock_logger:
            manager._validate_config()

            # Should have warning calls for missing API keys
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "API key" in str(call)
            ]
            assert len(warning_calls) > 0

    @patch("pathlib.Path.exists", return_value=False)
    def test_validate_config_missing_thermal_script(self, mock_exists):
        """Test validation warnings for missing thermal script"""
        manager = self.create_manager()

        config_dict = manager._get_default_config()
        manager.config = manager._dict_to_config(config_dict)

        with patch("src.config_manager.logger") as mock_logger:
            manager._validate_config()

            # Should warn about missing thermal script
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "Thermal performance script" in str(call)
            ]
            assert len(warning_calls) > 0

    def test_validate_config_invalid_timeouts(self):
        """Test validation of timeout values"""
        manager = self.create_manager()

        config_dict = manager._get_default_config()
        config_dict["claude_anthropic"]["timeout_seconds"] = -1
        config_dict["gemini"]["timeout_seconds"] = 500

        manager.config = manager._dict_to_config(config_dict)

        with patch("src.config_manager.logger") as mock_logger:
            manager._validate_config()

            # Should warn about invalid timeout values
            warning_calls = mock_logger.warning.call_args_list
            timeout_warnings = [
                call for call in warning_calls if "timeout" in str(call)
            ]
            assert len(timeout_warnings) > 0

    def test_load_config_full_flow(self):
        """Test full configuration loading flow"""
        config_data = {
            "claude_anthropic": {"enabled": True, "model": "custom-model"},
            "debug_mode": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            json_file_path = Path(f.name)

        try:
            with patch.dict(os.environ, {"MYCODER_THERMAL_MAX_TEMP": "82"}):
                manager = ConfigManager(json_file_path)
                config = manager.load_config()

                # Should merge file config, env config, and defaults
                assert config.claude_anthropic.enabled is True
                assert config.claude_anthropic.model == "custom-model"  # From file
                assert config.thermal.max_temp == 82  # From environment
                assert config.claude_oauth.enabled is True  # From defaults
                assert config.debug_mode is True  # From file

                # Config should be stored in manager
                assert manager.config is config

        finally:
            json_file_path.unlink()

    def test_save_config(self):
        """Test saving configuration to file"""
        manager = self.create_manager()

        # Load a basic config
        manager.config = manager._dict_to_config(manager._get_default_config())
        manager.config.debug_mode = True
        manager.config.preferred_provider = "gemini"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            save_path = Path(f.name)

        try:
            success = manager.save_config(save_path)
            assert success is True

            # Verify file was written correctly
            assert save_path.exists()

            with open(save_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["debug_mode"] is True
            assert saved_data["preferred_provider"] == "gemini"
            assert "claude_anthropic" in saved_data
            assert "thermal" in saved_data
            assert "system" in saved_data

        finally:
            if save_path.exists():
                save_path.unlink()

    def test_save_config_no_config(self):
        """Test saving when no config is loaded"""
        manager = self.create_manager()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
            save_path = Path(f.name)

        success = manager.save_config(save_path)
        assert success is False

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_save_config_permission_error(self, mock_open):
        """Test save config with permission error"""
        manager = self.create_manager()
        manager.config = manager._dict_to_config(manager._get_default_config())

        success = manager.save_config(Path("/restricted/config.json"))
        assert success is False

    def test_get_provider_config(self):
        """Test getting provider-specific configuration"""
        manager = self.create_manager()
        manager.config = manager._dict_to_config(manager._get_default_config())

        claude_config = manager.get_provider_config("claude_anthropic")
        assert claude_config is not None
        assert isinstance(claude_config, APIProviderSettings)
        assert claude_config.model == "claude-3-5-sonnet-20241022"

        invalid_config = manager.get_provider_config("nonexistent")
        assert invalid_config is None

    def test_get_provider_config_no_config(self):
        """Test getting provider config when no config loaded"""
        manager = self.create_manager()

        result = manager.get_provider_config("claude_anthropic")
        assert result is None

    def test_update_provider_config(self):
        """Test updating provider-specific configuration"""
        manager = self.create_manager()
        manager.config = manager._dict_to_config(manager._get_default_config())

        success = manager.update_provider_config(
            "claude_anthropic",
            {"enabled": False, "timeout_seconds": 60, "model": "claude-3-opus"},
        )

        assert success is True

        claude_config = manager.get_provider_config("claude_anthropic")
        assert claude_config.enabled is False
        assert claude_config.timeout_seconds == 60
        assert claude_config.model == "claude-3-opus"

    def test_update_provider_config_invalid_provider(self):
        """Test updating config for invalid provider"""
        manager = self.create_manager()
        manager.config = manager._dict_to_config(manager._get_default_config())

        success = manager.update_provider_config("nonexistent", {"enabled": False})
        assert success is False

    def test_update_provider_config_invalid_field(self):
        """Test updating config with invalid field"""
        manager = self.create_manager()
        manager.config = manager._dict_to_config(manager._get_default_config())

        with patch("src.config_manager.logger") as mock_logger:
            success = manager.update_provider_config(
                "claude_anthropic", {"enabled": False, "invalid_field": "value"}
            )

            assert success is True  # Should still succeed for valid fields

            # Should warn about invalid field
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "Unknown provider setting" in str(call)
            ]
            assert len(warning_calls) > 0

    def test_update_provider_config_no_config(self):
        """Test updating provider config when no config loaded"""
        manager = self.create_manager()

        success = manager.update_provider_config("claude_anthropic", {"enabled": False})
        assert success is False

    @patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "test_key", "GEMINI_API_KEY": "test_gemini"}
    )
    @patch("pathlib.Path.exists")
    def test_get_debug_info(self, mock_exists):
        """Test getting debug information"""
        mock_exists.return_value = True

        manager = self.create_manager()
        manager.config = manager._dict_to_config(manager._get_default_config())

        debug_info = manager.get_debug_info()

        assert debug_info["config_loaded"] is True
        assert "env_vars" in debug_info
        assert debug_info["env_vars"]["ANTHROPIC_API_KEY"] == "***"
        assert debug_info["env_vars"]["GEMINI_API_KEY"] == "***"
        assert "config_locations_checked" in debug_info
        assert debug_info["thermal_script_exists"] is True

    def test_get_debug_info_no_config(self):
        """Test debug info when no config loaded"""
        manager = self.create_manager(Path("/custom/config.json"))

        debug_info = manager.get_debug_info()

        assert debug_info["config_loaded"] is False
        assert debug_info["config_path"] == "/custom/config.json"
        assert debug_info["thermal_script_exists"] is False


class TestGlobalConfigFunctions:
    """Test global configuration functions"""

    def test_get_config_manager_singleton(self):
        """Test global config manager singleton"""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2  # Same instance
        assert isinstance(manager1, ConfigManager)

    def test_get_config_manager_with_path(self):
        """Test getting config manager with custom path"""
        custom_path = Path("/custom/config.json")
        manager = get_config_manager(custom_path)

        assert manager.config_path == custom_path

    def test_load_config_function(self):
        """Test load_config convenience function"""
        config_data = {
            "claude_anthropic": {"enabled": True, "model": "test-model"},
            "debug_mode": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            json_file_path = Path(f.name)

        try:
            config = load_config(json_file_path)

            assert isinstance(config, MyCoderConfig)
            assert config.claude_anthropic.enabled is True
            assert config.claude_anthropic.model == "test-model"
            assert config.debug_mode is True

        finally:
            json_file_path.unlink()


@pytest.mark.integration
class TestConfigManagerIntegration:
    """Integration tests for configuration manager"""

    def test_real_config_locations(self):
        """Test with real config file locations"""
        manager = ConfigManager()

        # Should not crash even if no config files exist
        file_config = manager._load_file_config()
        # Can be None if no config files exist
        assert file_config is None or isinstance(file_config, dict)

    def test_environment_integration(self):
        """Test integration with real environment variables"""
        # Test with actual environment
        manager = ConfigManager()
        env_config = manager._load_env_config()

        assert isinstance(env_config, dict)

        # If ANTHROPIC_API_KEY is set, should be in config
        if os.getenv("ANTHROPIC_API_KEY"):
            assert "anthropic" in env_config
            assert "api_key" in env_config["anthropic"]

    def test_full_load_realistic(self):
        """Test full config load in realistic scenario"""
        # Create temporary config file
        config_data = {
            "claude_anthropic": {"enabled": True, "timeout_seconds": 45},
            "thermal": {"enabled": True, "max_temp": 78},
            "debug_mode": False,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            json_file_path = Path(f.name)

        try:
            # Test with some environment overrides
            test_env = {"MYCODER_DEBUG_MODE": "true", "MYCODER_THERMAL_MAX_TEMP": "82"}

            with patch.dict(os.environ, test_env):
                manager = ConfigManager(json_file_path)
                config = manager.load_config()

                # Should have file config
                assert config.claude_anthropic.timeout_seconds == 45
                assert config.thermal.enabled is True

                # Should have environment overrides
                assert config.debug_mode is True  # Overridden by env
                assert config.thermal.max_temp == 82  # Overridden by env

                # Should have defaults for unspecified
                assert config.claude_oauth.enabled is True
                assert config.system.log_level == "INFO"

        finally:
            json_file_path.unlink()

    def test_config_save_load_roundtrip(self):
        """Test saving and loading config maintains data integrity"""
        # Create initial config
        manager1 = ConfigManager()
        original_config = manager1._dict_to_config(manager1._get_default_config())
        original_config.debug_mode = True
        original_config.preferred_provider = "gemini"
        original_config.claude_anthropic.timeout_seconds = 45
        original_config.thermal.max_temp = 78
        manager1.config = original_config

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            save_path = Path(f.name)

        try:
            # Save config
            success = manager1.save_config(save_path)
            assert success is True

            # Load with new manager
            manager2 = ConfigManager(save_path)
            loaded_config = manager2.load_config()

            # Should match original
            assert loaded_config.debug_mode == original_config.debug_mode
            assert (
                loaded_config.preferred_provider == original_config.preferred_provider
            )
            assert (
                loaded_config.claude_anthropic.timeout_seconds
                == original_config.claude_anthropic.timeout_seconds
            )
            assert loaded_config.thermal.max_temp == original_config.thermal.max_temp
            assert (
                loaded_config.claude_oauth.enabled
                == original_config.claude_oauth.enabled
            )

        finally:
            if save_path.exists():
                save_path.unlink()

    def test_config_validation_realistic(self):
        """Test configuration validation with realistic scenarios"""
        manager = ConfigManager()

        # Test with missing API keys (realistic scenario)
        with patch.dict(os.environ, {}, clear=True):
            config = manager.load_config()

            # Should still load successfully
            assert isinstance(config, MyCoderConfig)
            assert config.claude_anthropic.enabled is True  # Enabled by default
            assert config.gemini.enabled is True  # Enabled by default

            # Validation should complete (may have warnings)
            manager._validate_config()

    def test_provider_config_updates_realistic(self):
        """Test realistic provider configuration updates"""
        manager = ConfigManager()
        config = manager.load_config()

        # Test updating multiple provider settings
        updates = [
            ("claude_anthropic", {"enabled": False, "timeout_seconds": 60}),
            ("gemini", {"enabled": True, "model": "gemini-1.5-flash"}),
            ("ollama_local", {"timeout_seconds": 90, "model": "codellama"}),
        ]

        for provider_type, update_data in updates:
            success = manager.update_provider_config(provider_type, update_data)
            assert success is True

        # Verify all updates were applied
        assert manager.get_provider_config("claude_anthropic").enabled is False
        assert manager.get_provider_config("claude_anthropic").timeout_seconds == 60
        assert manager.get_provider_config("gemini").model == "gemini-1.5-flash"
        assert manager.get_provider_config("ollama_local").timeout_seconds == 90
        assert manager.get_provider_config("ollama_local").model == "codellama"
