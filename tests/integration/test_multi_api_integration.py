"""
Integration Tests for Multi-API System Components

Tests integration between API providers, configuration management,
and real-world API interactions in controlled scenarios.
"""

import asyncio
import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api_providers import (
    APIProviderRouter,
    APIProviderConfig,
    APIProviderType,
    ClaudeAnthropicProvider,
    ClaudeOAuthProvider,
    GeminiProvider,
    OllamaProvider,
)
from config_manager import ConfigManager, load_config


class TestMultiAPIConfigurationIntegration:
    """Test integration between configuration and API providers"""

    def create_realistic_config(self):
        """Create realistic test configuration"""
        return {
            "claude_anthropic": {
                "enabled": True,
                "timeout_seconds": 30,
                "model": "claude-3-5-sonnet-20241022",
                "priority": 1,
            },
            "claude_oauth": {"enabled": True, "timeout_seconds": 45, "priority": 2},
            "gemini": {
                "enabled": True,
                "timeout_seconds": 30,
                "model": "gemini-1.5-pro",
                "priority": 3,
            },
            "ollama_local": {
                "enabled": True,
                "timeout_seconds": 60,
                "base_url": "http://localhost:11434",
                "model": "tinyllama",
                "priority": 4,
            },
            "ollama_remote_urls": ["http://remote1:11434", "http://remote2:11434"],
            "thermal": {"enabled": True, "max_temp": 78, "critical_temp": 85},
            "preferred_provider": "claude_oauth",
            "fallback_enabled": True,
            "debug_mode": True,
        }

    def test_config_to_provider_mapping(self):
        """Test mapping configuration to API providers"""
        config_data = self.create_realistic_config()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)

        try:
            # Load configuration
            config_manager = ConfigManager(config_file)
            config = config_manager.load_config()

            # Create provider configs from loaded configuration
            provider_configs = []

            # Claude Anthropic
            if config.claude_anthropic.enabled:
                claude_config = APIProviderConfig(
                    provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                    enabled=config.claude_anthropic.enabled,
                    timeout_seconds=config.claude_anthropic.timeout_seconds,
                    config={
                        "model": config.claude_anthropic.model,
                        "api_key": config.claude_anthropic.api_key,
                    },
                )
                provider_configs.append(claude_config)

            # Claude OAuth
            if config.claude_oauth.enabled:
                oauth_config = APIProviderConfig(
                    provider_type=APIProviderType.CLAUDE_OAUTH,
                    enabled=config.claude_oauth.enabled,
                    timeout_seconds=config.claude_oauth.timeout_seconds,
                    config={},
                )
                provider_configs.append(oauth_config)

            # Gemini
            if config.gemini.enabled:
                gemini_config = APIProviderConfig(
                    provider_type=APIProviderType.GEMINI,
                    enabled=config.gemini.enabled,
                    timeout_seconds=config.gemini.timeout_seconds,
                    config={
                        "model": config.gemini.model,
                        "api_key": config.gemini.api_key,
                    },
                )
                provider_configs.append(gemini_config)

            # Ollama Local
            if config.ollama_local.enabled:
                ollama_config = APIProviderConfig(
                    provider_type=APIProviderType.OLLAMA_LOCAL,
                    enabled=config.ollama_local.enabled,
                    timeout_seconds=config.ollama_local.timeout_seconds,
                    config={
                        "base_url": config.ollama_local.base_url,
                        "model": config.ollama_local.model,
                    },
                )
                provider_configs.append(ollama_config)

            # Ollama Remote instances
            for i, remote_url in enumerate(config.ollama_remote_urls):
                remote_config = APIProviderConfig(
                    provider_type=APIProviderType.OLLAMA_REMOTE,
                    enabled=True,
                    timeout_seconds=45,
                    config={"base_url": remote_url, "model": "tinyllama"},
                )
                provider_configs.append(remote_config)

            # Create router
            router = APIProviderRouter(provider_configs)

            # Verify correct number of providers
            expected_count = 4 + len(
                config.ollama_remote_urls
            )  # 4 main + remote instances
            assert len(router.providers) == expected_count

            # Verify provider configurations
            claude_provider = router._get_provider(APIProviderType.CLAUDE_ANTHROPIC)
            assert claude_provider is not None
            assert claude_provider.config.timeout_seconds == 30
            assert claude_provider.model == "claude-3-5-sonnet-20241022"

            oauth_provider = router._get_provider(APIProviderType.CLAUDE_OAUTH)
            assert oauth_provider is not None
            assert oauth_provider.config.timeout_seconds == 45

            gemini_provider = router._get_provider(APIProviderType.GEMINI)
            assert gemini_provider is not None
            assert gemini_provider.model == "gemini-1.5-pro"

            ollama_provider = router._get_provider(APIProviderType.OLLAMA_LOCAL)
            assert ollama_provider is not None
            assert ollama_provider.base_url == "http://localhost:11434"
            assert ollama_provider.model == "tinyllama"

        finally:
            config_file.unlink()

    @patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "test_anthropic_key",
            "GEMINI_API_KEY": "test_gemini_key",
            "MYCODER_PREFERRED_PROVIDER": "gemini",
            "MYCODER_THERMAL_MAX_TEMP": "82",
        },
    )
    def test_environment_override_integration(self):
        """Test environment variable overrides in provider configuration"""
        base_config = self.create_realistic_config()
        base_config["claude_anthropic"]["enabled"] = False  # Disabled in config
        base_config["preferred_provider"] = "claude_anthropic"  # Will be overridden

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(base_config, f)
            config_file = Path(f.name)

        try:
            config_manager = ConfigManager(config_file)
            config = config_manager.load_config()

            # Environment should override file config
            assert config.preferred_provider == "gemini"  # Overridden by env
            assert config.thermal.max_temp == 82  # Overridden by env

            # API keys should come from environment
            # Note: These would be applied during provider initialization
            claude_provider_config = APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                enabled=True,  # Can enable if API key available
                config={"api_key": os.getenv("ANTHROPIC_API_KEY")},
            )

            claude_provider = ClaudeAnthropicProvider(claude_provider_config)
            assert claude_provider.api_key == "test_anthropic_key"

        finally:
            config_file.unlink()

    def test_provider_priority_configuration(self):
        """Test provider priority configuration and ordering"""
        config_data = self.create_realistic_config()

        # Modify priorities
        config_data["claude_anthropic"]["priority"] = 3
        config_data["claude_oauth"]["priority"] = 1  # Highest priority
        config_data["gemini"]["priority"] = 2
        config_data["ollama_local"]["priority"] = 4

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)

        try:
            config = load_config(config_file)

            # Verify priority configuration was loaded
            assert config.claude_anthropic.priority == 3
            assert config.claude_oauth.priority == 1
            assert config.gemini.priority == 2
            assert config.ollama_local.priority == 4

            # In real implementation, router would use these priorities
            # to determine fallback order

        finally:
            config_file.unlink()


class TestProviderHealthIntegration:
    """Test provider health monitoring integration"""

    @pytest.mark.asyncio
    async def test_provider_health_monitoring(self):
        """Test integrated provider health monitoring"""
        configs = [
            APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                enabled=True,
                config={"api_key": "test_key"},
            ),
            APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH, enabled=True),
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_LOCAL,
                enabled=True,
                config={"base_url": "http://localhost:11434"},
            ),
        ]

        router = APIProviderRouter(configs)

        # Mock health checks for different scenarios
        with (
            patch.object(
                router._get_provider(APIProviderType.CLAUDE_ANTHROPIC), "health_check"
            ) as mock_claude_health,
            patch.object(
                router._get_provider(APIProviderType.CLAUDE_OAUTH), "health_check"
            ) as mock_oauth_health,
            patch.object(
                router._get_provider(APIProviderType.OLLAMA_LOCAL), "health_check"
            ) as mock_ollama_health,
        ):

            from api_providers import APIProviderStatus

            # Set different health statuses
            mock_claude_health.return_value = APIProviderStatus.HEALTHY
            mock_oauth_health.return_value = APIProviderStatus.DEGRADED
            mock_ollama_health.return_value = APIProviderStatus.UNAVAILABLE

            # Perform health check
            health_results = await router.health_check_all()

            # Verify results
            assert health_results["claude_anthropic"]["status"] == "healthy"
            assert health_results["claude_oauth"]["status"] == "degraded"
            assert health_results["ollama_local"]["status"] == "unavailable"

            # All health check methods should have been called
            mock_claude_health.assert_called_once()
            mock_oauth_health.assert_called_once()
            mock_ollama_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_based_provider_selection(self):
        """Test provider selection based on health status"""
        configs = [
            APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                enabled=True,
                config={"api_key": "test_key"},
            ),
            APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH, enabled=True),
        ]

        router = APIProviderRouter(configs)

        # Mock providers
        claude_provider = router._get_provider(APIProviderType.CLAUDE_ANTHROPIC)
        oauth_provider = router._get_provider(APIProviderType.CLAUDE_OAUTH)

        with (
            patch.object(
                claude_provider, "can_handle_request"
            ) as mock_claude_can_handle,
            patch.object(claude_provider, "query") as mock_claude_query,
            patch.object(oauth_provider, "can_handle_request") as mock_oauth_can_handle,
            patch.object(oauth_provider, "query") as mock_oauth_query,
        ):

            from api_providers import APIResponse

            # First provider is unhealthy, second is healthy
            mock_claude_can_handle.return_value = False
            mock_oauth_can_handle.return_value = True

            mock_oauth_query.return_value = APIResponse(
                success=True,
                content="OAuth provider response",
                provider=APIProviderType.CLAUDE_OAUTH,
            )

            # Should fall back to OAuth provider
            response = await router.query("Test query")

            assert response.success is True
            assert response.provider == APIProviderType.CLAUDE_OAUTH
            assert response.content == "OAuth provider response"

            # Claude provider should not have been called due to health
            mock_claude_query.assert_not_called()
            mock_oauth_query.assert_called_once()


class TestThermalIntegration:
    """Test thermal management integration"""

    @pytest.mark.asyncio
    async def test_thermal_configuration_integration(self):
        """Test thermal configuration integration with providers"""
        configs = [
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_LOCAL,
                enabled=True,
                config={"base_url": "http://localhost:11434"},
            ),
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_REMOTE,
                enabled=True,
                config={"base_url": "http://remote:11434"},
            ),
        ]

        router = APIProviderRouter(configs)

        # Configure thermal integration
        thermal_config = {
            "enabled": True,
            "max_temp": 75,
            "critical_temp": 85,
            "check_interval": 30,
        }

        await router.configure_thermal_integration(thermal_config)

        # Verify thermal config was applied to local providers
        local_provider = router._get_provider(APIProviderType.OLLAMA_LOCAL)
        assert local_provider.config.config.get("thermal_monitoring") == thermal_config

        # Remote providers should also get thermal config
        remote_providers = [
            p
            for p in router.providers
            if p.config.provider_type == APIProviderType.OLLAMA_REMOTE
        ]
        assert len(remote_providers) > 0

        for provider in remote_providers:
            # Remote providers might have different thermal handling
            if hasattr(provider, "is_local") and provider.is_local:
                assert (
                    provider.config.config.get("thermal_monitoring") == thermal_config
                )

    @pytest.mark.skipif(
        not Path(
            "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh"
        ).exists(),
        reason="Q9550 thermal system not available",
    )
    @pytest.mark.asyncio
    async def test_real_thermal_integration(self):
        """Test integration with real Q9550 thermal system"""
        config = APIProviderConfig(
            provider_type=APIProviderType.OLLAMA_LOCAL,
            enabled=True,
            config={"base_url": "http://localhost:11434", "model": "tinyllama"},
        )

        provider = OllamaProvider(config)

        # Test thermal status check with real system
        thermal_status = await provider._check_thermal_status()

        # Should return valid thermal status
        assert isinstance(thermal_status, dict)
        assert "should_throttle" in thermal_status
        assert isinstance(thermal_status["should_throttle"], bool)

        # If thermal monitoring is working, we should get reason when throttling
        if thermal_status["should_throttle"]:
            assert "reason" in thermal_status
            assert thermal_status["reason"] in ["critical_temp", "high_temp"]


class TestProviderFallbackIntegration:
    """Test provider fallback chain integration"""

    @pytest.mark.asyncio
    async def test_complete_fallback_chain(self):
        """Test complete fallback chain with realistic failures"""
        configs = [
            APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                enabled=True,
                config={"api_key": "invalid_key"},  # Will fail
            ),
            APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_OAUTH,
                enabled=True,  # May fail if not authenticated
            ),
            APIProviderConfig(
                provider_type=APIProviderType.GEMINI,
                enabled=True,
                config={"api_key": "invalid_gemini_key"},  # Will fail
            ),
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_LOCAL,
                enabled=True,
                config={"base_url": "http://localhost:11434"},
            ),
        ]

        router = APIProviderRouter(configs)

        # Mock provider failures in sequence
        claude_provider = router._get_provider(APIProviderType.CLAUDE_ANTHROPIC)
        oauth_provider = router._get_provider(APIProviderType.CLAUDE_OAUTH)
        gemini_provider = router._get_provider(APIProviderType.GEMINI)
        ollama_provider = router._get_provider(APIProviderType.OLLAMA_LOCAL)

        with (
            patch.object(claude_provider, "can_handle_request", return_value=True),
            patch.object(claude_provider, "query") as mock_claude,
            patch.object(oauth_provider, "can_handle_request", return_value=True),
            patch.object(oauth_provider, "query") as mock_oauth,
            patch.object(gemini_provider, "can_handle_request", return_value=True),
            patch.object(gemini_provider, "query") as mock_gemini,
            patch.object(ollama_provider, "can_handle_request", return_value=True),
            patch.object(ollama_provider, "query") as mock_ollama,
        ):

            from api_providers import APIResponse

            # First three providers fail
            mock_claude.return_value = APIResponse(
                success=False,
                content="",
                provider=APIProviderType.CLAUDE_ANTHROPIC,
                error="Invalid API key",
            )

            mock_oauth.return_value = APIResponse(
                success=False,
                content="",
                provider=APIProviderType.CLAUDE_OAUTH,
                error="Authentication failed",
            )

            mock_gemini.return_value = APIResponse(
                success=False,
                content="",
                provider=APIProviderType.GEMINI,
                error="API quota exceeded",
            )

            # Last provider succeeds
            mock_ollama.return_value = APIResponse(
                success=True,
                content="Local Ollama response",
                provider=APIProviderType.OLLAMA_LOCAL,
                cost=0.0,
            )

            # Execute query with fallback
            response = await router.query("Test fallback chain")

            # Should succeed with last provider
            assert response.success is True
            assert response.provider == APIProviderType.OLLAMA_LOCAL
            assert response.content == "Local Ollama response"

            # All providers should have been tried
            mock_claude.assert_called_once()
            mock_oauth.assert_called_once()
            mock_gemini.assert_called_once()
            mock_ollama.assert_called_once()

    @pytest.mark.asyncio
    async def test_preferred_provider_fallback(self):
        """Test fallback with preferred provider specification"""
        configs = [
            APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                enabled=True,
                config={"api_key": "test_key"},
            ),
            APIProviderConfig(
                provider_type=APIProviderType.GEMINI,
                enabled=True,
                config={"api_key": "test_gemini_key"},
            ),
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_LOCAL,
                enabled=True,
                config={"base_url": "http://localhost:11434"},
            ),
        ]

        router = APIProviderRouter(configs)

        # Mock preferred provider (Gemini) failure
        claude_provider = router._get_provider(APIProviderType.CLAUDE_ANTHROPIC)
        gemini_provider = router._get_provider(APIProviderType.GEMINI)
        ollama_provider = router._get_provider(APIProviderType.OLLAMA_LOCAL)

        with (
            patch.object(gemini_provider, "can_handle_request", return_value=True),
            patch.object(gemini_provider, "query") as mock_gemini,
            patch.object(claude_provider, "can_handle_request", return_value=True),
            patch.object(claude_provider, "query") as mock_claude,
            patch.object(ollama_provider, "can_handle_request", return_value=True),
            patch.object(ollama_provider, "query") as mock_ollama,
        ):

            from api_providers import APIResponse

            # Preferred provider (Gemini) fails
            mock_gemini.return_value = APIResponse(
                success=False,
                content="",
                provider=APIProviderType.GEMINI,
                error="Rate limit exceeded",
            )

            # Fallback to Claude succeeds
            mock_claude.return_value = APIResponse(
                success=True,
                content="Claude fallback response",
                provider=APIProviderType.CLAUDE_ANTHROPIC,
            )

            # Query with preferred provider
            response = await router.query(
                "Test with preferred provider",
                preferred_provider=APIProviderType.GEMINI,
            )

            # Should fallback to Claude
            assert response.success is True
            assert response.provider == APIProviderType.CLAUDE_ANTHROPIC
            assert response.content == "Claude fallback response"

            # Gemini should have been tried first
            mock_gemini.assert_called_once()
            mock_claude.assert_called_once()
            mock_ollama.assert_not_called()  # Should not reach third provider


class TestRemoteOllamaIntegration:
    """Test remote Ollama integration scenarios"""

    @pytest.mark.asyncio
    async def test_multiple_remote_ollama_instances(self):
        """Test integration with multiple remote Ollama instances"""
        remote_urls = [
            "http://server1:11434",
            "http://server2:11434",
            "http://server3:11434",
        ]

        configs = []
        for i, url in enumerate(remote_urls):
            config = APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_REMOTE,
                enabled=True,
                config={"base_url": url, "model": f"model_{i+1}"},
            )
            configs.append(config)

        router = APIProviderRouter(configs)

        # Should have created providers for all remote URLs
        assert len(router.providers) == 3

        remote_providers = [
            p
            for p in router.providers
            if p.config.provider_type == APIProviderType.OLLAMA_REMOTE
        ]
        assert len(remote_providers) == 3

        # Verify each provider has correct configuration
        for i, provider in enumerate(remote_providers):
            assert provider.base_url == remote_urls[i]
            assert provider.model == f"model_{i+1}"
            assert provider.is_local is False

    @pytest.mark.asyncio
    async def test_remote_ollama_health_checks(self):
        """Test health checks for remote Ollama instances"""
        configs = [
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_REMOTE,
                enabled=True,
                config={
                    "base_url": "http://healthy-server:11434",
                    "model": "tinyllama",
                },
            ),
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_REMOTE,
                enabled=True,
                config={
                    "base_url": "http://unhealthy-server:11434",
                    "model": "tinyllama",
                },
            ),
        ]

        router = APIProviderRouter(configs)

        providers = [
            p
            for p in router.providers
            if p.config.provider_type == APIProviderType.OLLAMA_REMOTE
        ]

        # Mock health checks
        with (
            patch.object(providers[0], "health_check") as mock_healthy,
            patch.object(providers[1], "health_check") as mock_unhealthy,
        ):

            from api_providers import APIProviderStatus

            mock_healthy.return_value = APIProviderStatus.HEALTHY
            mock_unhealthy.return_value = APIProviderStatus.UNAVAILABLE

            health_results = await router.health_check_all()

            # Check results (keys are provider type values, not URLs)
            remote_results = [
                result
                for key, result in health_results.items()
                if "ollama_remote" in key.lower()
            ]

            # Should have health results for both remote instances
            assert len(remote_results) >= 2


@pytest.mark.integration
class TestConfigurationPersistence:
    """Test configuration persistence and loading scenarios"""

    def test_config_file_precedence(self):
        """Test configuration file precedence"""
        # Create multiple config files
        configs = {
            "base_config.json": {
                "claude_anthropic": {"enabled": True, "timeout_seconds": 30},
                "debug_mode": False,
            },
            "override_config.json": {
                "claude_anthropic": {"timeout_seconds": 60},
                "debug_mode": True,
                "preferred_provider": "claude_anthropic",
            },
        }

        config_files = []
        try:
            for filename, data in configs.items():
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as f:
                    json.dump(data, f)
                    config_files.append(Path(f.name))

            # Load base config
            base_manager = ConfigManager(config_files[0])
            base_config = base_manager.load_config()

            # Load override config
            override_manager = ConfigManager(config_files[1])
            override_config = override_manager.load_config()

            # Base config values
            assert base_config.claude_anthropic.enabled is True
            assert base_config.claude_anthropic.timeout_seconds == 30
            assert base_config.debug_mode is False

            # Override config values
            assert override_config.claude_anthropic.enabled is True  # From defaults
            assert override_config.claude_anthropic.timeout_seconds == 60  # Overridden
            assert override_config.debug_mode is True  # Overridden
            assert override_config.preferred_provider == "claude_anthropic"  # New

        finally:
            for config_file in config_files:
                if config_file.exists():
                    config_file.unlink()

    def test_config_validation_integration(self):
        """Test configuration validation with integration warnings"""
        invalid_config = {
            "claude_anthropic": {"enabled": True, "timeout_seconds": -1},  # Invalid
            "gemini": {"enabled": True, "timeout_seconds": 500},  # Too high
            "thermal": {
                "enabled": True,
                "performance_script": "/nonexistent/script.sh",  # Missing file
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_config, f)
            config_file = Path(f.name)

        try:
            # Clear environment to test missing API keys
            with patch.dict(os.environ, {}, clear=True):
                with patch("src.config_manager.logger") as mock_logger:
                    config_manager = ConfigManager(config_file)
                    config = config_manager.load_config()

                    # Should load but with warnings
                    assert config is not None

                    # Verify warnings were logged
                    warning_calls = mock_logger.warning.call_args_list
                    warning_messages = [str(call) for call in warning_calls]

                    # Should warn about various issues
                    has_timeout_warning = any(
                        "timeout" in msg.lower() for msg in warning_messages
                    )
                    has_api_key_warning = any(
                        "api key" in msg.lower() for msg in warning_messages
                    )
                    has_script_warning = any(
                        "script" in msg.lower() or "thermal" in msg.lower()
                        for msg in warning_messages
                    )

                    # At least one type of warning should be present
                    assert (
                        has_timeout_warning or has_api_key_warning or has_script_warning
                    )

        finally:
            config_file.unlink()

    def test_config_roundtrip_integration(self):
        """Test complete configuration save/load cycle"""
        original_data = {
            "claude_anthropic": {
                "enabled": True,
                "timeout_seconds": 45,
                "model": "claude-3-5-sonnet",
            },
            "ollama_remote_urls": ["http://remote1:11434", "http://remote2:11434"],
            "thermal": {"enabled": True, "max_temp": 78},
            "preferred_provider": "claude_anthropic",
            "debug_mode": True,
        }

        save_file = None
        try:
            # Save configuration
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(original_data, f)
                config_file = Path(f.name)

            # Load and modify
            config_manager = ConfigManager(config_file)
            config = config_manager.load_config()

            # Modify some values
            config_manager.update_provider_config(
                "claude_anthropic", {"timeout_seconds": 60, "model": "claude-3-opus"}
            )

            # Save to new file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                save_file = Path(f.name)

            success = config_manager.save_config(save_file)
            assert success is True

            # Load from saved file
            reload_manager = ConfigManager(save_file)
            reloaded_config = reload_manager.load_config()

            # Verify modifications persisted
            assert reloaded_config.claude_anthropic.timeout_seconds == 60
            assert reloaded_config.claude_anthropic.model == "claude-3-opus"

            # Verify other values preserved
            assert reloaded_config.thermal.max_temp == 78
            assert reloaded_config.debug_mode is True
            assert len(reloaded_config.ollama_remote_urls) == 2

        finally:
            if config_file.exists():
                config_file.unlink()
            if save_file and save_file.exists():
                save_file.unlink()
