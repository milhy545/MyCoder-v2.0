"""Configuration manager utilities for Enhanced MyCoder v2."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


def _default_performance_script_path() -> str:
    """Resolve the default thermal performance script path."""
    env_path = os.environ.get("MYCODER_PERFORMANCE_SCRIPT")
    if env_path:
        return env_path

    default_path = Path.home() / ".config" / "mycoder" / "performance_manager.sh"
    return str(default_path)


@dataclass
class APIProviderSettings:
    """Encapsulates provider-specific configuration."""

    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    priority: int = 10


@dataclass
class ThermalSettings:
    """Thermal management configuration."""

    enabled: bool = True
    max_temp: int = 80
    critical_temp: int = 85
    check_interval: int = 30
    throttle_on_high: bool = True
    emergency_shutdown: bool = False
    performance_script: str = ""


@dataclass
class SystemSettings:
    """General system-wide configuration."""

    working_directory: Optional[str] = None
    log_level: str = "INFO"
    session_timeout_hours: int = 24
    max_concurrent_requests: int = 10
    enable_tool_registry: bool = True
    enable_mcp_integration: bool = True


@dataclass
class MyCoderConfig:
    """Root configuration object consumed by the service."""

    claude_anthropic: APIProviderSettings
    claude_oauth: APIProviderSettings
    gemini: APIProviderSettings
    ollama_local: APIProviderSettings
    ollama_remote_urls: List[str] = field(default_factory=list)
    thermal: ThermalSettings = field(default_factory=ThermalSettings)
    system: SystemSettings = field(default_factory=SystemSettings)
    preferred_provider: str = "claude_anthropic"
    fallback_enabled: bool = True
    debug_mode: bool = False


class ConfigManager:
    """Helper to load, merge, validate, and persist configuration."""

    DEFAULT_CONFIG_LOCATIONS = [
        "mycoder_config.json",
        "config.json",
        "config.toml",
    ]
    _PROVIDER_FIELDS = {
        "enabled",
        "timeout_seconds",
        "max_retries",
        "model",
        "base_url",
        "api_key",
        "priority",
    }
    _ENV_SECTIONS = [
        "claude_anthropic",
        "claude_oauth",
        "gemini",
        "ollama_local",
        "thermal",
        "system",
    ]
    _API_KEY_ENV_MAPPING = {
        "ANTHROPIC_API_KEY": "claude_anthropic",
        "CLAUDE_OAUTH_API_KEY": "claude_oauth",
        "GEMINI_API_KEY": "gemini",
    }

    def __init__(self, config_path: Optional[Path | str] = None) -> None:
        self.config_path = Path(config_path) if config_path else None
        self.config: Optional[MyCoderConfig] = None
        self._env_prefix = "MYCODER_"

    def _get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration dictionary."""
        return {
            "claude_anthropic": {
                "enabled": True,
                "timeout_seconds": 30,
                "max_retries": 3,
                "model": "claude-3-5-sonnet-20241022",
                "priority": 1,
            },
            "claude_oauth": {
                "enabled": False,
                "timeout_seconds": 45,
                "max_retries": 3,
                "priority": 2,
            },
            "gemini": {
                "enabled": True,
                "timeout_seconds": 30,
                "max_retries": 3,
                "priority": 3,
            },
            "ollama_local": {
                "enabled": True,
                "timeout_seconds": 45,
                "max_retries": 3,
                "priority": 4,
                "base_url": "http://localhost:11434",
            },
            "ollama_remote_urls": [],
            "thermal": {
                "enabled": True,
                "max_temp": 80,
                "critical_temp": 85,
                "check_interval": 30,
                "throttle_on_high": True,
                "emergency_shutdown": False,
                "performance_script": _default_performance_script_path(),
            },
            "system": {
                "working_directory": None,
                "log_level": "INFO",
                "session_timeout_hours": 24,
                "max_concurrent_requests": 10,
                "enable_tool_registry": True,
                "enable_mcp_integration": True,
            },
            "preferred_provider": "claude_anthropic",
            "fallback_enabled": True,
            "debug_mode": False,
        }

    def _parse_env_value(self, raw_value: str) -> Any:
        """Parse a string from an env var into the most appropriate type."""
        value = raw_value.strip()

        if not value:
            return ""

        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"

        if "," in value:
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items

        try:
            int_value = int(value)
            return int_value
        except ValueError:
            pass

        try:
            float_value = float(value)
            return float_value
        except ValueError:
            pass

        return value

    def _apply_env_entry(
        self, config: Dict[str, Any], name: str, parsed_value: Any
    ) -> None:
        """Normalize env keys and write them into the config dictionary."""
        normalized = name.lower()
        prefix = self._env_prefix.lower()
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]

        if not normalized:
            return

        matched_section = next(
            (
                section
                for section in self._ENV_SECTIONS
                if normalized.startswith(section + "_")
            ),
            None,
        )

        if matched_section:
            field_name = normalized[len(matched_section) + 1 :]
            if not field_name:
                return
            section = config.setdefault(matched_section, {})
            section[field_name] = parsed_value
            return

        config[normalized] = parsed_value

    def _merge_deep(
        self, base: Dict[str, Any], overlay: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge `overlay` into `base` and return the result."""
        merged = dict(base)
        for key, value in overlay.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._merge_deep(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from the current environment variables."""
        config: Dict[str, Any] = {}
        for key, raw_value in os.environ.items():
            if not key.startswith(self._env_prefix):
                continue
            parsed = self._parse_env_value(raw_value)
            self._apply_env_entry(config, key, parsed)

        for env_key, provider in self._API_KEY_ENV_MAPPING.items():
            api_key = os.getenv(env_key)
            if api_key:
                section = config.setdefault(provider, {})
                section["api_key"] = api_key
                if provider == "claude_anthropic":
                    config.setdefault("anthropic", {})["api_key"] = api_key

        return config

    def _load_env_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration override values from an env-style file."""
        config: Dict[str, Any] = {}
        try:
            with path.open("r") as file_obj:
                for raw_line in file_obj:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    parsed = self._parse_env_value(value.strip())
                    normalized = key.strip().lower()
                    prefix = self._env_prefix.lower()
                    if normalized.startswith(prefix):
                        normalized = normalized[len(prefix) :]
                    if not normalized:
                        continue
                    config[normalized] = parsed
        except OSError:
            logger.warning("Unable to read env file %s", path, exc_info=True)

        return config

    def _load_file_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration from a JSON file."""
        candidates = []
        if self.config_path:
            candidates.append(self.config_path)
        else:
            candidates.extend(
                Path(location) for location in self.DEFAULT_CONFIG_LOCATIONS
            )

        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                with open(candidate, "r") as file_obj:
                    return json.load(file_obj)
            except PermissionError:
                logger.warning("Permission denied reading %s", candidate)
            except json.JSONDecodeError as exc:
                logger.warning("Unable to parse config file %s (%s)", candidate, exc)
            except OSError:
                logger.warning(
                    "Unable to open config file %s", candidate, exc_info=True
                )
        return None

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> MyCoderConfig:
        """Convert a dictionary into a MyCoderConfig object."""
        required_sections = [
            "claude_anthropic",
            "claude_oauth",
            "gemini",
            "ollama_local",
            "thermal",
            "system",
        ]

        for section in required_sections:
            if section not in config_dict:
                raise ValueError(f"Missing required configuration section '{section}'")

        def _provider_from_dict(section_name: str) -> APIProviderSettings:
            raw = config_dict.get(section_name) or {}
            merged = self._merge_deep(asdict(APIProviderSettings()), raw)
            filtered = {
                key: value
                for key, value in merged.items()
                if key in self._PROVIDER_FIELDS
            }
            return APIProviderSettings(**filtered)

        thermal_raw = config_dict.get("thermal", {})
        system_raw = config_dict.get("system", {})

        remote_urls_value = config_dict.get("ollama_remote_urls")
        if isinstance(remote_urls_value, list):
            remote_urls = remote_urls_value
        elif isinstance(remote_urls_value, str):
            remote_urls = [remote_urls_value]
        else:
            remote_urls = []

        return MyCoderConfig(
            claude_anthropic=_provider_from_dict("claude_anthropic"),
            claude_oauth=_provider_from_dict("claude_oauth"),
            gemini=_provider_from_dict("gemini"),
            ollama_local=_provider_from_dict("ollama_local"),
            ollama_remote_urls=remote_urls,
            thermal=ThermalSettings(**thermal_raw),
            system=SystemSettings(**system_raw),
            preferred_provider=config_dict.get(
                "preferred_provider", "claude_anthropic"
            ),
            fallback_enabled=config_dict.get("fallback_enabled", True),
            debug_mode=config_dict.get("debug_mode", False),
        )

    def _validate_config(self) -> None:
        """Run heuristic validation and emit warnings."""
        if not self.config:
            return

        for provider_name in ("claude_anthropic", "claude_oauth", "gemini"):
            provider = getattr(self.config, provider_name, None)
            if not provider:
                continue

            if provider.enabled and not provider.api_key:
                logger.warning("API key missing for provider %s", provider_name)

            if provider.timeout_seconds <= 0 or provider.timeout_seconds > 300:
                logger.warning(
                    "Provider %s has suspicious timeout %s",
                    provider_name,
                    provider.timeout_seconds,
                )

        script = self.config.thermal.performance_script
        if script and not Path(script).exists():
            logger.warning("Thermal performance script not found at %s", script)

    def load_config(self) -> MyCoderConfig:
        """Load configuration from defaults, files, and the environment."""
        defaults = self._get_default_config()
        file_config = self._load_file_config() or {}
        env_config = self._load_env_config()
        allow_env_overrides = file_config.get("env_overrides", True)

        merged = self._merge_deep(defaults, file_config)
        if allow_env_overrides:
            merged = self._merge_deep(merged, env_config)

        self.config = self._dict_to_config(merged)
        self._validate_config()
        return self.config

    def save_config(self, path: Path | str) -> bool:
        """Serialize current configuration to disk."""
        if not self.config:
            return False

        destination = Path(path)
        try:
            # Create a safe copy for serialization
            config_dict = asdict(self.config)

            # Redact sensitive keys to prevent leakage in config files
            # The system will reload them from Environment variables
            for provider in ["claude_anthropic", "claude_oauth", "gemini"]:
                if provider in config_dict and "api_key" in config_dict[provider]:
                    config_dict[provider]["api_key"] = ""

            config_dict.setdefault("env_overrides", False)

            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, "w") as file_obj:
                json.dump(config_dict, file_obj, indent=2)
            return True
        except PermissionError:
            logger.warning("Permission denied while saving config %s", destination)
        except OSError:
            logger.warning("Unable to write config file %s", destination, exc_info=True)

        return False

    def get_provider_config(self, provider_name: str) -> Optional[APIProviderSettings]:
        """Return a provider configuration if loaded."""
        if not self.config:
            return None
        return getattr(self.config, provider_name, None)

    def update_provider_config(
        self, provider_name: str, updates: Dict[str, Any]
    ) -> bool:
        """Update a provider configuration with new values."""
        provider = self.get_provider_config(provider_name)
        if not provider:
            return False

        success = False
        for key, value in updates.items():
            if key in self._PROVIDER_FIELDS:
                setattr(provider, key, value)
                success = True
            else:
                logger.warning("Unknown provider setting %s for %s", key, provider_name)

        return success

    def get_debug_info(self) -> Dict[str, Any]:
        """Expose helpful debugging insights."""
        env_keys = ["ANTHROPIC_API_KEY", "CLAUDE_OAUTH_API_KEY", "GEMINI_API_KEY"]
        env_vars = {key: "***" for key in env_keys if key in os.environ}

        script_exists = False
        if self.config and self.config.thermal.performance_script:
            script_exists = Path(self.config.thermal.performance_script).exists()

        return {
            "config_loaded": self.config is not None,
            "config_path": str(self.config_path) if self.config_path else None,
            "env_vars": env_vars,
            "config_locations_checked": list(self.DEFAULT_CONFIG_LOCATIONS),
            "thermal_script_exists": script_exists,
        }


_CONFIG_MANAGER_SINGLETON: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[Path | str] = None) -> ConfigManager:
    """Return a singleton configuration manager."""
    global _CONFIG_MANAGER_SINGLETON
    if config_path is None and _CONFIG_MANAGER_SINGLETON is not None:
        return _CONFIG_MANAGER_SINGLETON

    _CONFIG_MANAGER_SINGLETON = ConfigManager(config_path)
    return _CONFIG_MANAGER_SINGLETON


def load_config(config_path: Optional[Path | str] = None) -> MyCoderConfig:
    """Convenience helper to load configuration in one call."""
    return get_config_manager(config_path).load_config()
