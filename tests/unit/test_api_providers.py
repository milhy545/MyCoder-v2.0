"""
Comprehensive Unit Tests for API Providers System

Tests the multi-API provider system with all fallback scenarios,
error handling, and thermal integration for Q9550 systems.
"""

import os
import sys
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mycoder.api_providers import (
    APIProviderConfig,
    APIProviderRouter,
    APIProviderStatus,
    APIProviderType,
    APIResponse,
    BaseAPIProvider,
    ClaudeAnthropicProvider,
    ClaudeOAuthProvider,
    GeminiProvider,
    OllamaProvider,
)


class TestAPIResponse:
    """Test APIResponse data structure"""

    def test_api_response_creation(self):
        """Test APIResponse creation with all parameters"""
        response = APIResponse(
            success=True,
            content="Test content",
            provider=APIProviderType.CLAUDE_ANTHROPIC,
            cost=0.001,
            duration_ms=1500,
            tokens_used=100,
            session_id="test_session",
            metadata={"model": "claude-3-5-sonnet"},
            error=None,
        )

        assert response.success is True
        assert response.content == "Test content"
        assert response.provider == APIProviderType.CLAUDE_ANTHROPIC
        assert response.cost == 0.001
        assert response.duration_ms == 1500
        assert response.tokens_used == 100
        assert response.session_id == "test_session"
        assert response.metadata["model"] == "claude-3-5-sonnet"
        assert response.error is None

    def test_api_response_defaults(self):
        """Test APIResponse with default values"""
        response = APIResponse(
            success=True, content="Test", provider=APIProviderType.GEMINI
        )

        assert response.cost == 0.0
        assert response.duration_ms == 0
        assert response.tokens_used == 0
        assert response.session_id is None
        assert response.metadata == {}
        assert response.error is None

    def test_api_response_failure(self):
        """Test APIResponse for failure scenarios"""
        response = APIResponse(
            success=False,
            content="",
            provider=APIProviderType.OLLAMA_LOCAL,
            error="Connection failed",
        )

        assert response.success is False
        assert response.content == ""
        assert response.error == "Connection failed"


class TestAPIProviderConfig:
    """Test APIProviderConfig data structure"""

    def test_provider_config_creation(self):
        """Test APIProviderConfig creation"""
        config = APIProviderConfig(
            provider_type=APIProviderType.CLAUDE_ANTHROPIC,
            enabled=True,
            timeout_seconds=30,
            config={"api_key": "test_key"},
        )

        assert config.provider_type == APIProviderType.CLAUDE_ANTHROPIC
        assert config.enabled is True
        assert config.timeout_seconds == 30
        assert config.config["api_key"] == "test_key"

    def test_provider_config_defaults(self):
        """Test APIProviderConfig with default values"""
        config = APIProviderConfig(provider_type=APIProviderType.GEMINI)

        assert config.enabled is True
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.health_check_interval == 300
        assert config.config == {}


class TestBaseAPIProvider:
    """Test BaseAPIProvider abstract base class"""

    def create_test_provider(self):
        """Create a test provider implementation"""

        class TestProvider(BaseAPIProvider):
            async def query(self, prompt, context=None, **kwargs):
                return APIResponse(
                    success=True,
                    content="Test response",
                    provider=APIProviderType.CLAUDE_ANTHROPIC,
                )

            async def health_check(self):
                return APIProviderStatus.HEALTHY

        config = APIProviderConfig(provider_type=APIProviderType.CLAUDE_ANTHROPIC)
        return TestProvider(config)

    def test_provider_initialization(self):
        """Test provider initialization"""
        provider = self.create_test_provider()

        assert provider.config.provider_type == APIProviderType.CLAUDE_ANTHROPIC
        assert provider.status == APIProviderStatus.UNKNOWN
        assert provider.error_count == 0
        assert provider.total_requests == 0
        assert provider.successful_requests == 0

    @pytest.mark.asyncio
    async def test_can_handle_request_enabled(self):
        """Test can_handle_request when provider is enabled"""
        provider = self.create_test_provider()
        provider.config.enabled = True
        provider.status = APIProviderStatus.HEALTHY

        can_handle = await provider.can_handle_request()
        assert can_handle is True

    @pytest.mark.asyncio
    async def test_can_handle_request_disabled(self):
        """Test can_handle_request when provider is disabled"""
        provider = self.create_test_provider()
        provider.config.enabled = False

        can_handle = await provider.can_handle_request()
        assert can_handle is False

    @pytest.mark.asyncio
    async def test_can_handle_request_unavailable(self):
        """Test can_handle_request when provider is unavailable"""
        provider = self.create_test_provider()
        provider.config.enabled = True
        provider.status = APIProviderStatus.UNAVAILABLE

        can_handle = await provider.can_handle_request()
        assert can_handle is False

    def test_get_metrics(self):
        """Test provider metrics collection"""
        provider = self.create_test_provider()
        provider.total_requests = 10
        provider.successful_requests = 8
        provider.error_count = 2

        metrics = provider.get_metrics()

        assert metrics["provider"] == "claude_anthropic"
        assert metrics["total_requests"] == 10
        assert metrics["successful_requests"] == 8
        assert metrics["error_count"] == 2
        assert metrics["success_rate"] == 0.8


class TestClaudeAnthropicProvider:
    """Test Claude Anthropic API provider"""

    def create_provider(self, api_key="test_key"):
        """Create Claude Anthropic provider"""
        config = APIProviderConfig(
            provider_type=APIProviderType.CLAUDE_ANTHROPIC, config={"api_key": api_key}
        )
        return ClaudeAnthropicProvider(config)

    def test_provider_initialization(self):
        """Test Claude Anthropic provider initialization"""
        provider = self.create_provider()

        assert provider.api_key == "test_key"
        assert provider.base_url == "https://api.anthropic.com/v1"
        assert provider.model == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_health_check_no_api_key(self):
        """Test health check without API key"""
        provider = self.create_provider(api_key=None)

        status = await provider.health_check()
        assert status == APIProviderStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_query_no_api_key(self):
        """Test query without API key"""
        provider = self.create_provider(api_key=None)

        response = await provider.query("Hello")

        assert response.success is False
        assert "ANTHROPIC_API_KEY not configured" in response.error
        assert response.provider == APIProviderType.CLAUDE_ANTHROPIC

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_success(self, mock_post):
        """Test successful Claude API query"""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "content": [{"text": "Hello! How can I help you today?"}],
                "usage": {"input_tokens": 10, "output_tokens": 20},
            }
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        provider = self.create_provider()
        response = await provider.query("Hello")

        assert response.success is True
        assert response.content == "Hello! How can I help you today?"
        assert response.provider == APIProviderType.CLAUDE_ANTHROPIC
        assert response.tokens_used == 20
        assert response.cost > 0

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_function_call_executes_tools(self, mock_post, temp_dir):
        """Test Claude tool_use handling with tool execution loop"""
        tool_use_response = {
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool1",
                    "name": "file_read",
                    "input": {"path": "foo.txt"},
                }
            ],
            "usage": {"input_tokens": 5, "output_tokens": 0},
        }
        final_response = {
            "content": [{"text": "All set"}],
            "usage": {"input_tokens": 6, "output_tokens": 3},
        }

        first = AsyncMock()
        first.status = 200
        first.json = AsyncMock(return_value=tool_use_response)
        second = AsyncMock()
        second.status = 200
        second.json = AsyncMock(return_value=final_response)

        first_cm = AsyncMock()
        first_cm.__aenter__.return_value = first
        second_cm = AsyncMock()
        second_cm.__aenter__.return_value = second
        mock_post.side_effect = [first_cm, second_cm]

        class DummyTool:
            def to_anthropic_schema(self):
                return {
                    "name": "file_read",
                    "description": "Read file",
                    "input_schema": {"type": "object", "properties": {}},
                }

        execute_tool = AsyncMock(
            return_value=SimpleNamespace(
                success=True, data="content", metadata={"path": "foo.txt"}
            )
        )
        tool_registry = SimpleNamespace(
            tools={"file_read": DummyTool()}, execute_tool=execute_tool
        )

        provider = self.create_provider()
        response = await provider.query(
            "Hello",
            context={"tool_registry": tool_registry, "working_directory": temp_dir},
        )

        assert response.success is True
        assert response.content == "All set"
        execute_tool.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_function_call_multiple_tools(self, mock_post, temp_dir):
        """Test Claude tool_use handling with multiple tool calls"""
        tool_use_response = {
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool1",
                    "name": "file_read",
                    "input": {"path": "foo.txt"},
                },
                {
                    "type": "tool_use",
                    "id": "tool2",
                    "name": "file_write",
                    "input": {"path": "bar.txt", "content": "ok"},
                },
            ],
            "usage": {"input_tokens": 5, "output_tokens": 0},
        }
        final_response = {
            "content": [{"text": "Done"}],
            "usage": {"input_tokens": 6, "output_tokens": 3},
        }

        first = AsyncMock()
        first.status = 200
        first.json = AsyncMock(return_value=tool_use_response)
        second = AsyncMock()
        second.status = 200
        second.json = AsyncMock(return_value=final_response)

        first_cm = AsyncMock()
        first_cm.__aenter__.return_value = first
        second_cm = AsyncMock()
        second_cm.__aenter__.return_value = second
        mock_post.side_effect = [first_cm, second_cm]

        class DummyTool:
            def __init__(self, name):
                self.name = name

            def to_anthropic_schema(self):
                return {
                    "name": self.name,
                    "description": "Tool",
                    "input_schema": {"type": "object", "properties": {}},
                }

        execute_tool = AsyncMock(
            return_value=SimpleNamespace(success=True, data="ok", metadata={})
        )
        tool_registry = SimpleNamespace(
            tools={
                "file_read": DummyTool("file_read"),
                "file_write": DummyTool("file_write"),
            },
            execute_tool=execute_tool,
        )

        provider = self.create_provider()
        response = await provider.query(
            "Hello",
            context={"tool_registry": tool_registry, "working_directory": temp_dir},
        )

        assert response.success is True
        assert response.content == "Done"
        assert execute_tool.await_count == 2

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_api_error(self, mock_post):
        """Test Claude API error handling"""
        # Mock API error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Invalid request")
        mock_post.return_value.__aenter__.return_value = mock_response

        provider = self.create_provider()
        response = await provider.query("Hello")

        assert response.success is False
        assert "API error 400" in response.error
        assert response.provider == APIProviderType.CLAUDE_ANTHROPIC

    @pytest.mark.asyncio
    async def test_process_file_context(self):
        """Test file context processing"""
        provider = self.create_provider()

        # Create temporary test files
        test_dir = Path("/tmp/test_mycoder")
        test_dir.mkdir(exist_ok=True)

        file1 = test_dir / "test1.py"
        file1.write_text("print('Hello World')")

        file2 = test_dir / "test2.py"
        file2.write_text("def hello():\n    return 'Hello'")

        files = [file1, file2]
        content = await provider._process_file_context(files)

        assert "test1.py" in content
        assert "test2.py" in content
        assert "print('Hello World')" in content
        assert "def hello()" in content

        # Cleanup
        file1.unlink()
        file2.unlink()
        test_dir.rmdir()

    def test_calculate_cost(self):
        """Test cost calculation"""
        provider = self.create_provider()

        usage = {"input_tokens": 1000, "output_tokens": 500}
        cost = provider._calculate_cost(usage)

        # Expected cost: 1000 * 0.000003 + 500 * 0.000015 = 0.003 + 0.0075 = 0.0105
        assert abs(cost - 0.0105) < 0.0001


class TestClaudeOAuthProvider:
    """Test Claude OAuth provider"""

    def create_provider(self):
        """Create Claude OAuth provider"""
        config = APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH)
        return ClaudeOAuthProvider(config)

    @pytest.mark.asyncio
    async def test_get_auth_manager_import_error(self):
        """Test auth manager import error handling"""
        provider = self.create_provider()

        with patch(
            "builtins.__import__", side_effect=ImportError("claude-cli-auth not found")
        ):
            with pytest.raises(ImportError):
                await provider._get_auth_manager()

    @pytest.mark.asyncio
    @patch("mycoder.providers.llm.anthropic.ClaudeAuthManager")
    async def test_query_success(self, mock_auth_manager_class):
        """Test successful OAuth query"""
        # Mock claude-cli-auth response
        mock_response = Mock()
        mock_response.content = "Hello from Claude!"
        mock_response.cost = 0.001
        mock_response.duration_ms = 1500
        mock_response.num_turns = 1
        mock_response.tools_used = []
        mock_response.session_id = "test_session"

        mock_auth_manager = AsyncMock()
        mock_auth_manager.query = AsyncMock(return_value=mock_response)
        mock_auth_manager_class.return_value = mock_auth_manager

        provider = self.create_provider()
        response = await provider.query("Hello")

        assert response.success is True
        assert response.content == "Hello from Claude!"
        assert response.provider == APIProviderType.CLAUDE_OAUTH
        assert response.cost == 0.001
        assert response.session_id == "test_session"

    @pytest.mark.asyncio
    @patch("mycoder.providers.llm.anthropic.ClaudeAuthManager")
    async def test_query_error(self, mock_auth_manager_class):
        """Test OAuth query error handling"""
        mock_auth_manager = AsyncMock()
        mock_auth_manager.query = AsyncMock(side_effect=Exception("Auth failed"))
        mock_auth_manager_class.return_value = mock_auth_manager

        provider = self.create_provider()
        response = await provider.query("Hello")

        assert response.success is False
        assert "Auth failed" in response.error
        assert response.provider == APIProviderType.CLAUDE_OAUTH


class TestGeminiProvider:
    """Test Google Gemini API provider"""

    def create_provider(self, api_key="test_key"):
        """Create Gemini provider"""
        config = APIProviderConfig(
            provider_type=APIProviderType.GEMINI, config={"api_key": api_key}
        )
        return GeminiProvider(config)

    def test_provider_initialization(self):
        """Test Gemini provider initialization"""
        provider = self.create_provider()

        assert provider.api_key == "test_key"
        assert provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
        assert provider.model == "gemini-1.5-pro"

    @pytest.mark.asyncio
    async def test_query_no_api_key(self):
        """Test query without API key"""
        with patch.dict(os.environ, {}, clear=True):
            provider = self.create_provider(api_key=None)

            response = await provider.query("Hello")

            assert response.success is False
            assert "GEMINI_API_KEY not configured" in response.error

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_success(self, mock_post):
        """Test successful Gemini API query"""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "Hello! I'm Gemini, how can I assist you?"}
                            ]
                        }
                    }
                ],
                "usageMetadata": {
                    "totalTokenCount": 50,
                    "promptTokenCount": 5,
                    "candidatesTokenCount": 45,
                },
            }
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        provider = self.create_provider()
        response = await provider.query("Hello")

        assert response.success is True
        assert response.content == "Hello! I'm Gemini, how can I assist you?"
        assert response.provider == APIProviderType.GEMINI
        assert response.tokens_used == 50

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_function_call_executes_tools(self, mock_post, temp_dir):
        """Test Gemini functionCall handling with tool execution loop"""
        tool_call_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "file_read",
                                    "args": {"path": "foo.txt"},
                                }
                            }
                        ]
                    }
                }
            ]
        }
        final_response = {
            "candidates": [{"content": {"parts": [{"text": "Done"}]}}],
            "usageMetadata": {"totalTokenCount": 7},
        }

        first = AsyncMock()
        first.status = 200
        first.json = AsyncMock(return_value=tool_call_response)
        second = AsyncMock()
        second.status = 200
        second.json = AsyncMock(return_value=final_response)

        first_cm = AsyncMock()
        first_cm.__aenter__.return_value = first
        second_cm = AsyncMock()
        second_cm.__aenter__.return_value = second
        mock_post.side_effect = [first_cm, second_cm]

        class DummyTool:
            def to_gemini_schema(self):
                return {
                    "name": "file_read",
                    "description": "Read file",
                    "parameters": {"type": "object", "properties": {}},
                }

        execute_tool = AsyncMock(
            return_value=SimpleNamespace(
                success=True, data="content", metadata={"path": "foo.txt"}
            )
        )
        tool_registry = SimpleNamespace(
            tools={"file_read": DummyTool()}, execute_tool=execute_tool
        )

        provider = self.create_provider()
        response = await provider.query(
            "Hello",
            context={"tool_registry": tool_registry, "working_directory": temp_dir},
        )

        assert response.success is True
        assert response.content == "Done"
        execute_tool.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_function_call_skips_when_none(self, mock_post, temp_dir):
        """Test Gemini tool loop is skipped when no functionCall exists"""
        initial_response = {
            "candidates": [{"content": {"parts": [{"text": "Hello there"}]}}],
            "usageMetadata": {"totalTokenCount": 4},
        }

        first = AsyncMock()
        first.status = 200
        first.json = AsyncMock(return_value=initial_response)
        first_cm = AsyncMock()
        first_cm.__aenter__.return_value = first
        mock_post.return_value = first_cm

        class DummyTool:
            def to_gemini_schema(self):
                return {
                    "name": "file_read",
                    "description": "Read file",
                    "parameters": {"type": "object", "properties": {}},
                }

        execute_tool = AsyncMock()
        tool_registry = SimpleNamespace(
            tools={"file_read": DummyTool()}, execute_tool=execute_tool
        )

        provider = self.create_provider()
        response = await provider.query(
            "Hello",
            context={"tool_registry": tool_registry, "working_directory": temp_dir},
        )

        assert response.success is True
        assert response.content == "Hello there"
        execute_tool.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_no_candidates(self, mock_post):
        """Test Gemini response with no candidates"""
        # Mock response with no candidates
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"candidates": []})
        mock_post.return_value.__aenter__.return_value = mock_response

        provider = self.create_provider()
        response = await provider.query("Hello")

        assert response.success is False
        assert "No response candidates" in response.error

    def test_calculate_cost(self):
        """Test Gemini cost calculation"""
        provider = self.create_provider()

        usage = {"totalTokenCount": 1000}
        cost = provider._calculate_cost(usage)

        assert cost == 0.001  # 1000 * 0.000001


class TestOllamaProvider:
    """Test Ollama provider (local and remote)"""

    def create_local_provider(self):
        """Create local Ollama provider"""
        config = APIProviderConfig(
            provider_type=APIProviderType.OLLAMA_LOCAL,
            config={"base_url": "http://localhost:11434", "model": "tinyllama"},
        )
        return OllamaProvider(config)

    def create_remote_provider(self):
        """Create remote Ollama provider"""
        config = APIProviderConfig(
            provider_type=APIProviderType.OLLAMA_REMOTE,
            config={"base_url": "http://remote-server:11434", "model": "tinyllama"},
        )
        return OllamaProvider(config)

    def test_local_provider_initialization(self):
        """Test local Ollama provider initialization"""
        provider = self.create_local_provider()

        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "tinyllama"
        assert provider.is_local is True

    def test_remote_provider_initialization(self):
        """Test remote Ollama provider initialization"""
        provider = self.create_remote_provider()

        assert provider.base_url == "http://remote-server:11434"
        assert provider.model == "tinyllama"
        assert provider.is_local is False

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_query_success(self, mock_post):
        """Test successful Ollama query"""
        # Mock successful Ollama response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "response": "Hello! I'm a local AI assistant.",
                "eval_count": 25,
                "eval_duration": 1500000000,  # nanoseconds
            }
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        provider = self.create_local_provider()
        response = await provider.query("Hello")

        assert response.success is True
        assert response.content == "Hello! I'm a local AI assistant."
        assert response.provider == APIProviderType.OLLAMA_LOCAL
        assert response.tokens_used == 25
        assert response.cost == 0.0  # Ollama is free

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_health_check_success(self, mock_get):
        """Test successful health check"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        provider = self.create_local_provider()
        status = await provider.health_check()

        assert status == APIProviderStatus.HEALTHY

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_health_check_failure(self, mock_get):
        """Test failed health check"""
        mock_get.side_effect = Exception("Connection refused")

        provider = self.create_local_provider()
        status = await provider.health_check()

        assert status == APIProviderStatus.UNAVAILABLE

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_check_thermal_status_local(self, mock_subprocess):
        """Test thermal status check for local provider"""
        # Mock thermal script success
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Temperature: 75°C - NORMAL"
        mock_subprocess.return_value = mock_result

        provider = self.create_local_provider()
        thermal_status = await provider._check_thermal_status()

        assert thermal_status["should_throttle"] is False

    @pytest.mark.asyncio
    @patch("os.path.exists", return_value=True)
    @patch("os.environ.get", return_value="/fake/thermal_script.sh")
    @patch("subprocess.run")
    async def test_check_thermal_status_critical(
        self, mock_subprocess, mock_env, mock_exists
    ):
        """Test thermal status check with critical temperature"""
        # Mock thermal script with critical temperature
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Temperature: 87°C - CRITICAL"
        mock_subprocess.return_value = mock_result

        provider = self.create_local_provider()
        thermal_status = await provider._check_thermal_status()

        assert thermal_status["should_throttle"] is True
        assert thermal_status["reason"] == "critical_temp"

    @pytest.mark.asyncio
    @patch("os.path.exists", return_value=True)
    @patch("os.environ.get", return_value="/fake/thermal_script.sh")
    @patch("subprocess.run")
    async def test_thermal_aware_query(self, mock_subprocess, mock_env, mock_exists):
        """Test query with thermal monitoring"""
        # Mock thermal script indicating high temperature
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Temperature: 82°C - HIGH"
        mock_subprocess.return_value = mock_result

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"response": "Throttled response", "eval_count": 10}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            provider = self.create_local_provider()
            context = {"thermal_monitoring": True}
            response = await provider.query("Hello", context=context)

            assert response.success is True
            # Verify that thermal monitoring was triggered
            mock_subprocess.assert_called()


class TestAPIProviderRouter:
    """Test API provider router with fallback logic"""

    def create_router(self):
        """Create router with test providers"""
        configs = [
            APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                config={"api_key": "test_key"},
            ),
            APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH),
            APIProviderConfig(
                provider_type=APIProviderType.GEMINI,
                config={"api_key": "test_gemini_key"},
            ),
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_LOCAL,
                config={"base_url": "http://localhost:11434"},
            ),
        ]
        return APIProviderRouter(configs)

    def test_router_initialization(self):
        """Test router initialization"""
        router = self.create_router()

        assert len(router.providers) == 4
        assert len(router.fallback_chain) == 4
        assert router.fallback_chain[0] == APIProviderType.CLAUDE_ANTHROPIC
        assert router.fallback_chain[-1] == APIProviderType.OLLAMA_LOCAL

    def test_get_provider(self):
        """Test getting provider by type"""
        router = self.create_router()

        claude_provider = router._get_provider(APIProviderType.CLAUDE_ANTHROPIC)
        assert claude_provider is not None
        assert isinstance(claude_provider, ClaudeAnthropicProvider)

        non_existent = router._get_provider(APIProviderType.OLLAMA_REMOTE)
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_query_preferred_provider_success(self):
        """Test query with preferred provider success"""
        router = self.create_router()

        # Mock successful response from preferred provider
        with (
            patch.object(
                router._get_provider(APIProviderType.GEMINI),
                "can_handle_request",
                return_value=True,
            ),
            patch.object(
                router._get_provider(APIProviderType.GEMINI), "query"
            ) as mock_query,
        ):

            mock_query.return_value = APIResponse(
                success=True, content="Gemini response", provider=APIProviderType.GEMINI
            )

            response = await router.query(
                "Hello", preferred_provider=APIProviderType.GEMINI
            )

            assert response.success is True
            assert response.content == "Gemini response"
            assert response.provider == APIProviderType.GEMINI

    @pytest.mark.asyncio
    async def test_query_fallback_chain(self):
        """Test query with fallback chain"""
        router = self.create_router()

        # Mock first provider failing, second provider succeeding
        claude_provider = router._get_provider(APIProviderType.CLAUDE_ANTHROPIC)
        oauth_provider = router._get_provider(APIProviderType.CLAUDE_OAUTH)

        with (
            patch.object(claude_provider, "can_handle_request", return_value=True),
            patch.object(claude_provider, "query") as mock_claude_query,
            patch.object(oauth_provider, "can_handle_request", return_value=True),
            patch.object(oauth_provider, "query") as mock_oauth_query,
        ):

            # First provider fails
            mock_claude_query.return_value = APIResponse(
                success=False,
                content="",
                provider=APIProviderType.CLAUDE_ANTHROPIC,
                error="API key invalid",
            )

            # Second provider succeeds
            mock_oauth_query.return_value = APIResponse(
                success=True,
                content="OAuth success",
                provider=APIProviderType.CLAUDE_OAUTH,
            )

            response = await router.query("Hello")

            assert response.success is True
            assert response.content == "OAuth success"
            assert response.provider == APIProviderType.CLAUDE_OAUTH

    @pytest.mark.asyncio
    async def test_query_all_providers_fail(self):
        """Test query when all providers fail"""
        router = self.create_router()

        # Mock all providers failing
        with ExitStack() as stack:
            for provider in router.providers:
                stack.enter_context(
                    patch.object(provider, "can_handle_request", return_value=False)
                )

            response = await router.query("Hello")

        assert response.success is False
        assert response.provider == APIProviderType.RECOVERY
        assert "All providers failed" in response.error

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health check for all providers"""
        router = self.create_router()

        # Mock health checks for all providers
        with (
            patch.object(
                router._get_provider(APIProviderType.CLAUDE_ANTHROPIC),
                "health_check",
                return_value=APIProviderStatus.HEALTHY,
            ),
            patch.object(
                router._get_provider(APIProviderType.CLAUDE_OAUTH),
                "health_check",
                return_value=APIProviderStatus.DEGRADED,
            ),
            patch.object(
                router._get_provider(APIProviderType.GEMINI),
                "health_check",
                return_value=APIProviderStatus.UNAVAILABLE,
            ),
            patch.object(
                router._get_provider(APIProviderType.OLLAMA_LOCAL),
                "health_check",
                return_value=APIProviderStatus.HEALTHY,
            ),
        ):

            health_results = await router.health_check_all()

            assert health_results["claude_anthropic"]["status"] == "healthy"
            assert health_results["claude_oauth"]["status"] == "degraded"
            assert health_results["gemini"]["status"] == "unavailable"
            assert health_results["ollama_local"]["status"] == "healthy"

    def test_get_available_providers(self):
        """Test getting available providers"""
        router = self.create_router()

        # Set some providers as healthy
        router._get_provider(APIProviderType.CLAUDE_ANTHROPIC).status = (
            APIProviderStatus.HEALTHY
        )
        router._get_provider(APIProviderType.OLLAMA_LOCAL).status = (
            APIProviderStatus.HEALTHY
        )
        router._get_provider(APIProviderType.GEMINI).status = (
            APIProviderStatus.UNAVAILABLE
        )

        available = router.get_available_providers()

        assert APIProviderType.CLAUDE_ANTHROPIC in available
        assert APIProviderType.OLLAMA_LOCAL in available
        assert APIProviderType.GEMINI not in available

    @pytest.mark.asyncio
    async def test_configure_thermal_integration(self):
        """Test thermal integration configuration"""
        router = self.create_router()

        thermal_config = {"enabled": True, "max_temp": 80, "check_interval": 30}

        await router.configure_thermal_integration(thermal_config)

        # Verify thermal config was applied to local Ollama providers
        local_provider = router._get_provider(APIProviderType.OLLAMA_LOCAL)
        assert local_provider.config.config["thermal_monitoring"] == thermal_config


@pytest.mark.integration
class TestAPIProvidersIntegration:
    """Integration tests for API providers with real Q9550 thermal system"""

    @pytest.mark.asyncio
    async def test_thermal_integration_real(self):
        """Test real thermal integration with Q9550 system"""
        # Skip if not on Q9550 system
        thermal_script = Path(
            "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh"
        )
        if not thermal_script.exists():
            pytest.skip("Thermal management script not available")

        config = APIProviderConfig(
            provider_type=APIProviderType.OLLAMA_LOCAL,
            config={"base_url": "http://localhost:11434", "model": "tinyllama"},
        )
        provider = OllamaProvider(config)

        # Test thermal status check
        thermal_status = await provider._check_thermal_status()

        assert "should_throttle" in thermal_status
        assert isinstance(thermal_status["should_throttle"], bool)

    @pytest.mark.asyncio
    async def test_full_fallback_chain_realistic(self):
        """Test realistic fallback chain scenario"""
        configs = [
            APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                enabled=False,  # Simulate no API key
            ),
            APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH, enabled=True),
            APIProviderConfig(
                provider_type=APIProviderType.OLLAMA_LOCAL,
                config={"base_url": "http://localhost:11434", "model": "tinyllama"},
            ),
        ]

        router = APIProviderRouter(configs)

        # This will test actual fallback behavior in realistic conditions
        response = await router.query("Hello, can you respond briefly?")

        # Should get a response from one of the providers
        assert response is not None
        assert isinstance(response, APIResponse)
