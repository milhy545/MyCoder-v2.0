"""
Configuration Manager for Enhanced MyCoder v2.0

Manages configuration for multi-API providers, thermal management,
and system settings with support for multiple configuration sources.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class APIProviderSettings:
    """Settings for individual API providers"""

    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    priority: int = 10  # Lower number = higher priority


@dataclass
class ThermalSettings:
    """Thermal management settings for Q9550 systems"""

    enabled: bool = True
    max_temp: int = 80
    critical_temp: int = 85
    check_interval: int = 30
    throttle_on_high: bool = True
    emergency_shutdown: bool = False
    performance_script: str = (
        "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh"
    )


@dataclass
class SystemSettings:
    """General system settings"""

    working_directory: Optional[str] = None
    log_level: str = "INFO"
    session_timeout_hours: int = 24
    max_concurrent_requests: int = 10
    enable_tool_registry: bool = True
    enable_mcp_integration: bool = True


@dataclass
class MyCoderConfig:
    """Complete MyCoder v2.0 configuration"""

    # API Provider Settings
    claude_anthropic: APIProviderSettings = None
    claude_oauth: APIProviderSettings = None
    gemini: APIProviderSettings = None
    ollama_local: APIProviderSettings = None
    ollama_remote_urls: List[str] = None

    inception_mercury: APIProviderSettings = None

    # System Settings
    thermal: ThermalSettings = None
    system: SystemSettings = None

    # Runtime Settings
    preferred_provider: Optional[str] = None
    fallback_enabled: bool = True
    debug_mode: bool = False

    def __post_init__(self):
        """Initialize default values if not provided"""
        if self.claude_anthropic is None:
            self.claude_anthropic = APIProviderSettings(enabled=False)
        if self.claude_oauth is None:
            self.claude_oauth = APIProviderSettings(enabled=True)
        if self.gemini is None:
            self.gemini = APIProviderSettings(enabled=False)
        if self.ollama_local is None:
            self.ollama_local = APIProviderSettings(
                enabled=True, base_url="http://localhost:11434"
            )
        if self.ollama_remote_urls is None:
            self.ollama_remote_urls = []
        if self.inception_mercury is None:
            self.inception_mercury = APIProviderSettings(enabled=False)
        if self.thermal is None:
            self.thermal = ThermalSettings()
        if self.system is None:
            self.system = SystemSettings()


class ConfigManager:
    """Configuration manager with multiple source support"""

    DEFAULT_CONFIG_LOCATIONS = [
        Path.home() / ".mycoder" / "config.json",
        Path.home() / ".config" / "mycoder" / "config.json",
        Path.cwd() / "mycoder_config.json",
        Path.cwd() / ".env.mycoder",
    ]

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.config: Optional[MyCoderConfig] = None
        self._env_prefix = "MYCODER_"

    def load_config(self) -> MyCoderConfig:
        """Load configuration from all available sources"""
        logger.info("Loading MyCoder v2.0 configuration...")

        # Start with default configuration
        config_dict = self._get_default_config()

        # Overlay file-based configuration
        file_config = self._load_file_config()
        if file_config:
            expanded_file_config = self._expand_env_config(file_config)
            config_dict = self._merge_deep(config_dict, expanded_file_config)

        # Overlay environment variables
        env_config = self._load_env_config()
        if env_config:
            expanded_env_config = self._expand_env_config(env_config)
            config_dict = self._merge_deep(config_dict, expanded_env_config)

        # Create configuration object
        self.config = self._dict_to_config(config_dict)

        # Validate configuration
        self._validate_config()

        logger.info("Configuration loaded successfully")
        return self.config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            "claude_anthropic": {
                "enabled": True,
                "timeout_seconds": 30,
                "max_retries": 3,
                "model": "claude-3-5-sonnet-20241022",
                "priority": 1,
            },
            "claude_oauth": {
                "enabled": True,
                "timeout_seconds": 45,
                "max_retries": 3,
                "priority": 2,
            },
            "gemini": {
                "enabled": True,
                "timeout_seconds": 30,
                "max_retries": 3,
                "model": "gemini-1.5-pro",
                "priority": 3,
            },
            "ollama_local": {
                "enabled": True,
                "timeout_seconds": 60,
                "max_retries": 2,
                "model": "tinyllama",
                "base_url": "http://localhost:11434",
                "priority": 4,
            },
            "ollama_remote_urls": [],
            "thermal": {
                "enabled": True,
                "max_temp": 80,
                "critical_temp": 85,
                "check_interval": 30,
                "throttle_on_high": True,
                "emergency_shutdown": False,
                "performance_script": "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh",
            },
                "system": {
                    "log_level": "INFO",
                    "session_timeout_hours": 24,
                    "max_concurrent_requests": 10,
                    "enable_tool_registry": True,
                    "enable_mcp_integration": True,
                },
                "inception_mercury": {
                    "enabled": False,
                    "model": "mercury",
                    "base_url": "https://api.inceptionlabs.ai/v1",
                    "timeout_seconds": 60,
                    "realtime": False,
                    "diffusing": False,
                    "tools": [],
                },
            "preferred_provider": None,
            "fallback_enabled": True,
            "debug_mode": False,
        }

    def _load_file_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration from file sources"""
        config_locations = (
            [self.config_path] if self.config_path else self.DEFAULT_CONFIG_LOCATIONS
        )

        for location in config_locations:
            if location and location.exists():
                try:
                    logger.info(f"Loading configuration from: {location}")

                    if location.suffix == ".json":
                        with open(location, "r") as f:
                            return json.load(f)
                    elif location.name.endswith(".env") or "env" in location.name:
                        return self._load_env_file(location)

                except Exception as e:
                    logger.warning(f"Failed to load config from {location}: {e}")

        logger.info("No configuration file found, using defaults")
        return None

    def _load_env_file(self, env_file: Path) -> Dict[str, Any]:
        """Load configuration from environment file"""
        config = {}

        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")

                    if key.startswith(self._env_prefix):
                        config_key = key[len(self._env_prefix) :].lower()
                        config[config_key] = self._parse_env_value(value)

        return config

    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {}

        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                config_key = key[len(self._env_prefix) :].lower()
                config[config_key] = self._parse_env_value(value)

        # Special handling for API keys
        api_keys = {
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),  # For future use
            "inception_api_key": os.getenv("INCEPTION_API_KEY"),
        }

        for key, value in api_keys.items():
            if value:
                provider_name = key.split("_")[0]
                provider_config = config.get(provider_name)
                if not isinstance(provider_config, dict):
                    provider_config = {}
                provider_config["api_key"] = value
                config[provider_name] = provider_config

        return config

    def _expand_env_config(self, env_config: Dict[str, Any]) -> Dict[str, Any]:
        """Expand flat env-style config keys into nested config structure."""
        expanded: Dict[str, Any] = {}
        top_level_keys = {
            "preferred_provider",
            "fallback_enabled",
            "debug_mode",
            "ollama_remote_urls",
            "network_check_host",
            "network_check_port",
        }
        section_keys = {
            "claude_anthropic",
            "claude_oauth",
            "gemini",
            "ollama_local",
            "thermal",
            "system",
            "inception_mercury",
        }
        provider_prefixes = [
            "claude_anthropic",
            "claude_oauth",
            "gemini",
            "ollama_local",
            "inception_mercury",
        ]

        for key, value in env_config.items():
            if key in top_level_keys:
                expanded[key] = value
                continue

            if key in section_keys and isinstance(value, dict):
                expanded[key] = value
                continue

            if key in ("anthropic", "gemini") and isinstance(value, dict):
                provider_key = "claude_anthropic" if key == "anthropic" else "gemini"
                expanded.setdefault(provider_key, {}).update(value)
                continue

            matched_provider = None
            for prefix in provider_prefixes:
                prefix_token = f"{prefix}_"
                if key.startswith(prefix_token):
                    matched_provider = prefix
                    suffix = key[len(prefix_token) :]
                    expanded.setdefault(matched_provider, {})[suffix] = value
                    break

            if matched_provider:
                continue

            if key.startswith("thermal_"):
                expanded.setdefault("thermal", {})[key[len("thermal_") :]] = value
                continue

            if key.startswith("system_"):
                expanded.setdefault("system", {})[key[len("system_") :]] = value
                continue

            legacy_map = {
                "claude_model": ("claude_anthropic", "model"),
                "claude_timeout_seconds": ("claude_anthropic", "timeout_seconds"),
                "gemini_model": ("gemini", "model"),
                "ollama_local_model": ("ollama_local", "model"),
                "ollama_local_url": ("ollama_local", "base_url"),
                "ollama_local_base_url": ("ollama_local", "base_url"),
            }
            if key in legacy_map:
                provider_key, field_name = legacy_map[key]
                expanded.setdefault(provider_key, {})[field_name] = value
                continue

            expanded[key] = value

        return expanded

    def _parse_env_value(self, value: str) -> Union[str, int, float, bool, List[str]]:
        """Parse environment variable value to appropriate type"""
        # Boolean values
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Numeric values
        if value.isdigit():
            return int(value)

        try:
            return float(value)
        except ValueError:
            pass

        # List values (comma-separated)
        if "," in value:
            return [item.strip() for item in value.split(",")]

        # String values
        return value

    def _merge_deep(
        self, base: Dict[str, Any], overlay: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries"""
        result = base.copy()

        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_deep(result[key], value)
            else:
                result[key] = value

        return result

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> MyCoderConfig:
        """Convert configuration dictionary to MyCoderConfig object"""
        try:
            if not config_dict:
                raise ValueError("Configuration dictionary is empty")
            # Create individual settings objects
            claude_anthropic = APIProviderSettings(
                **config_dict.get("claude_anthropic", {})
            )
            claude_oauth = APIProviderSettings(**config_dict.get("claude_oauth", {}))
            gemini = APIProviderSettings(**config_dict.get("gemini", {}))
            ollama_local = APIProviderSettings(**config_dict.get("ollama_local", {}))
            inception_mercury = APIProviderSettings(
                **config_dict.get("inception_mercury", {})
            )

            thermal = ThermalSettings(**config_dict.get("thermal", {}))
            system = SystemSettings(**config_dict.get("system", {}))

            return MyCoderConfig(
                claude_anthropic=claude_anthropic,
                claude_oauth=claude_oauth,
                gemini=gemini,
                ollama_local=ollama_local,
                inception_mercury=inception_mercury,
                ollama_remote_urls=config_dict.get("ollama_remote_urls", []),
                thermal=thermal,
                system=system,
                preferred_provider=config_dict.get("preferred_provider"),
                fallback_enabled=config_dict.get("fallback_enabled", True),
                debug_mode=config_dict.get("debug_mode", False),
            )

        except Exception as e:
            logger.error(f"Failed to parse configuration: {e}")
            raise ValueError(f"Invalid configuration format: {e}")

    def _validate_config(self):
        """Validate configuration for common issues"""
        if not self.config:
            return

        # Check API key availability
        if (
            self.config.claude_anthropic.enabled
            and not self.config.claude_anthropic.api_key
        ):
            if not os.getenv("ANTHROPIC_API_KEY"):
                logger.warning("Claude Anthropic enabled but no API key found")

        if self.config.gemini.enabled and not self.config.gemini.api_key:
            if not os.getenv("GEMINI_API_KEY"):
                logger.warning("Gemini enabled but no API key found")

        if (
            self.config.inception_mercury
            and self.config.inception_mercury.enabled
            and not self.config.inception_mercury.api_key
        ):
            if not os.getenv("INCEPTION_API_KEY"):
                logger.warning("Inception Mercury enabled but no API key found")

        # Check thermal script availability
        if self.config.thermal.enabled:
            script_path = Path(self.config.thermal.performance_script)
            if not script_path.exists():
                logger.warning(f"Thermal performance script not found: {script_path}")

        # Check working directory
        if self.config.system.working_directory:
            work_dir = Path(self.config.system.working_directory)
            if not work_dir.exists():
                logger.warning(f"Working directory not found: {work_dir}")

        # Validate timeout values
        providers = [
            self.config.claude_anthropic,
            self.config.claude_oauth,
            self.config.gemini,
            self.config.ollama_local,
            self.config.inception_mercury,
        ]
        for provider in providers:
            if provider.timeout_seconds <= 0:
                logger.warning("Provider timeout must be positive")
            if provider.timeout_seconds > 300:
                logger.warning("Provider timeout very high (>5 minutes)")

    def save_config(self, config_path: Optional[Path] = None) -> bool:
        """Save current configuration to file"""
        if not self.config:
            logger.error("No configuration to save")
            return False

        save_path = config_path or self.config_path
        if not save_path:
            save_path = self.DEFAULT_CONFIG_LOCATIONS[0]

        try:
            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary
            config_dict = {
                "claude_anthropic": asdict(self.config.claude_anthropic),
                "claude_oauth": asdict(self.config.claude_oauth),
                "gemini": asdict(self.config.gemini),
                "ollama_local": asdict(self.config.ollama_local),
                "inception_mercury": asdict(self.config.inception_mercury),
                "ollama_remote_urls": self.config.ollama_remote_urls,
                "thermal": asdict(self.config.thermal),
                "system": asdict(self.config.system),
                "preferred_provider": self.config.preferred_provider,
                "fallback_enabled": self.config.fallback_enabled,
                "debug_mode": self.config.debug_mode,
            }

            # Save as JSON
            with open(save_path, "w") as f:
                json.dump(config_dict, f, indent=2)

            logger.info(f"Configuration saved to: {save_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def get_provider_config(self, provider_type: str) -> Optional[APIProviderSettings]:
        """Get configuration for specific provider"""
        if not self.config:
            return None

        provider_map = {
            "claude_anthropic": self.config.claude_anthropic,
            "claude_oauth": self.config.claude_oauth,
            "gemini": self.config.gemini,
            "ollama_local": self.config.ollama_local,
            "inception_mercury": self.config.inception_mercury,
        }

        return provider_map.get(provider_type)

    def update_provider_config(
        self, provider_type: str, updates: Dict[str, Any]
    ) -> bool:
        """Update configuration for specific provider"""
        if not self.config:
            return False

        provider = self.get_provider_config(provider_type)
        if not provider:
            return False

        # Update provider settings
        for key, value in updates.items():
            if hasattr(provider, key):
                setattr(provider, key, value)
            else:
                logger.warning(f"Unknown provider setting: {key}")

        return True

    def get_debug_info(self) -> Dict[str, Any]:
        """Get debugging information about configuration"""
        return {
            "config_loaded": self.config is not None,
            "config_path": str(self.config_path) if self.config_path else None,
            "env_vars": {
                "ANTHROPIC_API_KEY": "***" if os.getenv("ANTHROPIC_API_KEY") else None,
                "GEMINI_API_KEY": "***" if os.getenv("GEMINI_API_KEY") else None,
                "MYCODER_*": [k for k in os.environ.keys() if k.startswith("MYCODER_")],
            },
            "config_locations_checked": [
                str(loc) for loc in self.DEFAULT_CONFIG_LOCATIONS
            ],
            "thermal_script_exists": (
                Path(
                    self.config.thermal.performance_script if self.config else ""
                ).exists()
                if self.config
                else False
            ),
        }


# Global configuration instance
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[Path] = None) -> ConfigManager:
    """Get the global configuration manager instance"""
    global _global_config_manager
    if _global_config_manager is None or (
        config_path and _global_config_manager.config_path != config_path
    ):
        _global_config_manager = ConfigManager(config_path)
    return _global_config_manager


def load_config(config_path: Optional[Path] = None) -> MyCoderConfig:
    """Load and return MyCoder configuration"""
    manager = get_config_manager(config_path)
    return manager.load_config()
