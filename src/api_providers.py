"""
Multi-API Provider System for MyCoder v2.0

This module implements a 5-tier API provider system with intelligent fallbacks:
1. Claude Anthropic API (direct API key)
2. Claude OAuth (claude-cli-auth subscription)
3. Gemini API (Google AI)
4. Ollama Local (localhost:11434)
5. Ollama Remote (configurable remote URLs)

Inspired by FEI architecture patterns for distributed AI systems.
"""

import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path

import aiohttp
import json

logger = logging.getLogger(__name__)


class APIProviderType(Enum):
    """API provider types in priority order"""

    CLAUDE_ANTHROPIC = "claude_anthropic"
    CLAUDE_OAUTH = "claude_oauth"
    GEMINI = "gemini"
    OLLAMA_LOCAL = "ollama_local"
    OLLAMA_REMOTE = "ollama_remote"
    RECOVERY = "recovery"


class APIProviderStatus(Enum):
    """Provider status for health monitoring"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class APIResponse:
    """Standardized API response across all providers"""

    success: bool
    content: str
    provider: APIProviderType
    cost: float = 0.0
    duration_ms: int = 0
    tokens_used: int = 0
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class APIProviderConfig:
    """Configuration for API providers"""

    provider_type: APIProviderType
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    health_check_interval: int = 300  # 5 minutes
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class BaseAPIProvider(ABC):
    """Base class for all API providers with FEI-inspired patterns"""

    def __init__(self, config: APIProviderConfig):
        self.config = config
        self.status = APIProviderStatus.UNKNOWN
        self.last_health_check = 0
        self.error_count = 0
        self.total_requests = 0
        self.successful_requests = 0

    @abstractmethod
    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        """Execute query with provider-specific implementation"""
        pass

    @abstractmethod
    async def health_check(self) -> APIProviderStatus:
        """Check provider health and availability"""
        pass

    async def can_handle_request(self, context: Dict[str, Any] = None) -> bool:
        """Check if provider can handle the request"""
        if not self.config.enabled:
            return False

        # Perform health check if needed
        now = time.time()
        if self.status == APIProviderStatus.UNKNOWN or (
            self.last_health_check
            and (now - self.last_health_check) > self.config.health_check_interval
        ):
            self.status = await self.health_check()
            self.last_health_check = now

        return self.status in [APIProviderStatus.HEALTHY, APIProviderStatus.DEGRADED]

    def get_metrics(self) -> Dict[str, Any]:
        """Get provider performance metrics"""
        success_rate = 0
        if self.total_requests > 0:
            success_rate = self.successful_requests / self.total_requests

        return {
            "provider": self.config.provider_type.value,
            "status": self.status.value,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "last_health_check": self.last_health_check,
        }


class ClaudeAnthropicProvider(BaseAPIProvider):
    """Claude API provider using direct Anthropic API"""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.api_key = config.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = config.config.get("base_url", "https://api.anthropic.com/v1")
        self.model = config.config.get("model", "claude-3-5-sonnet-20241022")

    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        """Execute query using Anthropic API"""
        self.total_requests += 1
        start_time = time.time()

        try:
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }

            messages = [{"role": "user", "content": prompt}]

            # Add file context if provided
            if context and context.get("files"):
                file_content = await self._process_file_context(context["files"])
                if file_content:
                    messages[0]["content"] = f"{file_content}\n\n{prompt}"

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "temperature": kwargs.get("temperature", 0.7),
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                async with session.post(
                    f"{self.base_url}/messages", headers=headers, json=payload
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API error {response.status}: {error_text}")

                    result = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            return APIResponse(
                success=True,
                content=result["content"][0]["text"],
                provider=APIProviderType.CLAUDE_ANTHROPIC,
                cost=self._calculate_cost(result.get("usage", {})),
                duration_ms=duration_ms,
                tokens_used=result.get("usage", {}).get("output_tokens", 0),
                session_id=kwargs.get("session_id"),
                metadata={"model": self.model, "usage": result.get("usage", {})},
            )

        except Exception as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"Claude Anthropic API error: {e}")

            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.CLAUDE_ANTHROPIC,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        """Check Claude Anthropic API health"""
        try:
            if not self.api_key:
                return APIProviderStatus.UNAVAILABLE

            # Simple test query
            test_response = await self.query("Hello", timeout_seconds=10)

            if test_response.success:
                return APIProviderStatus.HEALTHY
            else:
                return APIProviderStatus.DEGRADED

        except Exception as e:
            logger.warning(f"Claude Anthropic health check failed: {e}")
            return APIProviderStatus.UNAVAILABLE

    async def _process_file_context(self, files: List[Path]) -> str:
        """Process file context for Claude API"""
        file_contents = []
        for file_path in files[:5]:  # Limit to 5 files
            try:
                if file_path.exists() and file_path.is_file():
                    content = file_path.read_text(encoding="utf-8")[:8000]  # Limit size
                    file_contents.append(f"File: {file_path.name}\n```\n{content}\n```")
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")

        return "\n\n".join(file_contents) if file_contents else ""

    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """Calculate API cost based on token usage"""
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        # Claude 3.5 Sonnet pricing (as of 2024)
        input_cost_per_token = 0.000003  # $3 per million tokens
        output_cost_per_token = 0.000015  # $15 per million tokens

        return (input_tokens * input_cost_per_token) + (
            output_tokens * output_cost_per_token
        )


class ClaudeOAuthProvider(BaseAPIProvider):
    """Claude provider using claude-cli-auth OAuth"""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self._auth_manager = None

    async def _get_auth_manager(self):
        """Lazy load claude-cli-auth to avoid circular imports"""
        if self._auth_manager is None:
            try:
                from claude_cli_auth import ClaudeAuthManager

                self._auth_manager = ClaudeAuthManager()
            except ImportError as e:
                raise ImportError("claude-cli-auth not available") from e
        return self._auth_manager

    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        """Execute query using Claude OAuth"""
        self.total_requests += 1
        start_time = time.time()

        try:
            auth_manager = await self._get_auth_manager()

            # Prepare arguments for claude-cli-auth
            auth_kwargs = {"timeout": self.config.timeout_seconds}

            if context:
                if context.get("working_directory"):
                    auth_kwargs["working_directory"] = context["working_directory"]
                if context.get("files"):
                    auth_kwargs["files"] = [str(f) for f in context["files"]]

            if kwargs.get("session_id"):
                auth_kwargs["session_id"] = kwargs["session_id"]
                auth_kwargs["continue_session"] = kwargs.get("continue_session", False)

            # Execute query
            response = await auth_manager.query(prompt, **auth_kwargs)

            duration_ms = int((time.time() - start_time) * 1000)

            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            return APIResponse(
                success=True,
                content=response.content,
                provider=APIProviderType.CLAUDE_OAUTH,
                cost=response.cost,
                duration_ms=response.duration_ms,
                tokens_used=getattr(response, "tokens_used", 0),
                session_id=response.session_id,
                metadata={
                    "num_turns": response.num_turns,
                    "tools_used": response.tools_used,
                },
            )

        except Exception as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"Claude OAuth error: {e}")

            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.CLAUDE_OAUTH,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        """Check Claude OAuth health"""
        try:
            auth_manager = await self._get_auth_manager()

            # Test simple query
            test_response = await auth_manager.query("Hello", timeout=10)

            if hasattr(test_response, "content") and test_response.content:
                return APIProviderStatus.HEALTHY
            else:
                return APIProviderStatus.DEGRADED

        except Exception as e:
            logger.warning(f"Claude OAuth health check failed: {e}")
            return APIProviderStatus.UNAVAILABLE


class GeminiProvider(BaseAPIProvider):
    """Google Gemini API provider"""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.api_key = config.config.get("api_key") or os.getenv("GEMINI_API_KEY")
        self.base_url = config.config.get(
            "base_url", "https://generativelanguage.googleapis.com/v1beta"
        )
        self.model = config.config.get("model", "gemini-1.5-pro")

    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        """Execute query using Gemini API"""
        self.total_requests += 1
        start_time = time.time()

        try:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not configured")

            # Build full prompt with file context
            full_prompt = prompt
            if context and context.get("files"):
                file_content = await self._process_file_context(context["files"])
                if file_content:
                    full_prompt = f"{file_content}\n\n{prompt}"

            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "maxOutputTokens": kwargs.get("max_tokens", 4096),
                    "topP": kwargs.get("top_p", 0.8),
                    "topK": kwargs.get("top_k", 40),
                },
            }

            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                async with session.post(url, json=payload) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Gemini API error {response.status}: {error_text}"
                        )

                    result = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            if "candidates" not in result or not result["candidates"]:
                raise Exception("No response candidates from Gemini")

            content = result["candidates"][0]["content"]["parts"][0]["text"]

            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            return APIResponse(
                success=True,
                content=content,
                provider=APIProviderType.GEMINI,
                cost=self._calculate_cost(result.get("usageMetadata", {})),
                duration_ms=duration_ms,
                tokens_used=result.get("usageMetadata", {}).get("totalTokenCount", 0),
                session_id=kwargs.get("session_id"),
                metadata={
                    "model": self.model,
                    "usage": result.get("usageMetadata", {}),
                },
            )

        except Exception as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"Gemini API error: {e}")

            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.GEMINI,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        """Check Gemini API health"""
        try:
            if not self.api_key:
                return APIProviderStatus.UNAVAILABLE

            test_response = await self.query("Hello", timeout_seconds=10)

            if test_response.success:
                return APIProviderStatus.HEALTHY
            else:
                return APIProviderStatus.DEGRADED

        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return APIProviderStatus.UNAVAILABLE

    async def _process_file_context(self, files: List[Path]) -> str:
        """Process file context for Gemini API"""
        file_contents = []
        for file_path in files[:5]:  # Limit to 5 files
            try:
                if file_path.exists() and file_path.is_file():
                    content = file_path.read_text(encoding="utf-8")[:8000]  # Limit size
                    file_contents.append(f"File: {file_path.name}\n{content}\n")
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")

        return "\n".join(file_contents) if file_contents else ""

    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """Calculate Gemini API cost based on token usage"""
        total_tokens = usage.get("totalTokenCount", 0)

        # Gemini 1.5 Pro pricing (as of 2024) - simplified
        cost_per_token = 0.000001  # Approximate cost

        return total_tokens * cost_per_token


class OllamaProvider(BaseAPIProvider):
    """Ollama provider for local and remote instances"""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.base_url = config.config.get("base_url", "http://localhost:11434")
        self.model = config.config.get("model", "tinyllama")
        self.is_local = "localhost" in self.base_url or "127.0.0.1" in self.base_url

    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        """Execute query using Ollama"""
        self.total_requests += 1
        start_time = time.time()

        try:
            # Build full prompt with file context
            full_prompt = prompt
            if context and context.get("files"):
                file_content = await self._process_file_context(context["files"])
                if file_content:
                    full_prompt = f"Context:\n{file_content}\n\nQuery: {prompt}"

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 2048),
                },
            }

            # For local instances, add thermal monitoring integration
            if self.is_local and context and context.get("thermal_monitoring"):
                # Check thermal status before long operations
                temp_check = await self._check_thermal_status()
                if temp_check["should_throttle"]:
                    payload["options"]["num_predict"] = min(
                        payload["options"]["num_predict"], 512
                    )

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                async with session.post(
                    f"{self.base_url}/api/generate", json=payload
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama error {response.status}: {error_text}")

                    result = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            provider_type = (
                APIProviderType.OLLAMA_LOCAL
                if self.is_local
                else APIProviderType.OLLAMA_REMOTE
            )

            return APIResponse(
                success=True,
                content=result.get("response", ""),
                provider=provider_type,
                cost=0.0,  # Ollama is typically free
                duration_ms=duration_ms,
                tokens_used=result.get("eval_count", 0),
                session_id=kwargs.get("session_id"),
                metadata={
                    "model": self.model,
                    "base_url": self.base_url,
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0),
                },
            )

        except Exception as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"Ollama error ({self.base_url}): {e}")

            provider_type = (
                APIProviderType.OLLAMA_LOCAL
                if self.is_local
                else APIProviderType.OLLAMA_REMOTE
            )

            return APIResponse(
                success=False,
                content="",
                provider=provider_type,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        """Check Ollama instance health"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(f"{self.base_url}/api/version") as response:
                    if response.status == 200:
                        return APIProviderStatus.HEALTHY
                    else:
                        return APIProviderStatus.DEGRADED

        except Exception as e:
            logger.warning(f"Ollama health check failed ({self.base_url}): {e}")
            return APIProviderStatus.UNAVAILABLE

    async def _process_file_context(self, files: List[Path]) -> str:
        """Process file context for Ollama"""
        file_contents = []
        for file_path in files[:3]:  # Limit for smaller models
            try:
                if file_path.exists() and file_path.is_file():
                    content = file_path.read_text(encoding="utf-8")[
                        :2000
                    ]  # Smaller limit
                    file_contents.append(f"{file_path.name}: {content}")
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")

        return "\n".join(file_contents) if file_contents else ""

    async def _check_thermal_status(self) -> Dict[str, Any]:
        """Check thermal status for local instances (Q9550 integration)"""
        try:
            # Import thermal management from PowerManagement system
            import subprocess

            result = subprocess.run(
                [
                    "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh",
                    "status",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # Parse thermal status
                if "CRITICAL" in result.stdout:
                    return {"should_throttle": True, "reason": "critical_temp"}
                elif "HIGH" in result.stdout:
                    return {"should_throttle": True, "reason": "high_temp"}

            return {"should_throttle": False}

        except Exception as e:
            logger.warning(f"Thermal check failed: {e}")
            return {"should_throttle": False}


class APIProviderRouter:
    """FEI-inspired router for managing multiple API providers"""

    def __init__(self, configs: List[APIProviderConfig]):
        self.providers: List[BaseAPIProvider] = []
        self.fallback_chain: List[APIProviderType] = []
        self._initialize_providers(configs)

    def _initialize_providers(self, configs: List[APIProviderConfig]):
        """Initialize all configured providers"""
        provider_classes = {
            APIProviderType.CLAUDE_ANTHROPIC: ClaudeAnthropicProvider,
            APIProviderType.CLAUDE_OAUTH: ClaudeOAuthProvider,
            APIProviderType.GEMINI: GeminiProvider,
            APIProviderType.OLLAMA_LOCAL: OllamaProvider,
            APIProviderType.OLLAMA_REMOTE: OllamaProvider,
        }

        for config in configs:
            if config.provider_type in provider_classes:
                try:
                    provider = provider_classes[config.provider_type](config)
                    self.providers.append(provider)
                    self.fallback_chain.append(config.provider_type)
                    logger.info(f"Initialized provider: {config.provider_type.value}")
                except Exception as e:
                    logger.error(
                        f"Failed to initialize {config.provider_type.value}: {e}"
                    )

        logger.info(f"Initialized {len(self.providers)} API providers")
        logger.info(f"Fallback chain: {[p.value for p in self.fallback_chain]}")

    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        preferred_provider: APIProviderType = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query with intelligent provider selection and fallbacks"""

        # Determine provider order
        provider_order = []

        if preferred_provider and preferred_provider in self.fallback_chain:
            # Start with preferred provider
            provider_order.append(preferred_provider)
            # Add remaining providers in fallback order
            provider_order.extend(
                [p for p in self.fallback_chain if p != preferred_provider]
            )
        else:
            # Use default fallback order
            provider_order = self.fallback_chain.copy()

        logger.info(f"Query execution order: {[p.value for p in provider_order]}")

        last_error = None

        for provider_type in provider_order:
            provider = self._get_provider(provider_type)
            if not provider:
                continue

            try:
                # Check if provider can handle request
                can_handle = await provider.can_handle_request(context)
                if not can_handle:
                    logger.info(f"Provider {provider_type.value} cannot handle request")
                    continue

                logger.info(f"Attempting query with {provider_type.value}")
                response = await provider.query(prompt, context, **kwargs)

                if response.success:
                    logger.info(f"Query successful with {provider_type.value}")
                    return response
                else:
                    logger.warning(
                        f"Provider {provider_type.value} returned error: {response.error}"
                    )
                    last_error = response.error

            except Exception as e:
                logger.error(f"Provider {provider_type.value} failed: {e}")
                last_error = str(e)
                continue

        # All providers failed
        logger.error("All API providers failed")
        return APIResponse(
            success=False,
            content="",
            provider=APIProviderType.RECOVERY,
            error=f"All providers failed. Last error: {last_error}",
            metadata={"attempted_providers": [p.value for p in provider_order]},
        )

    def _get_provider(
        self, provider_type: APIProviderType
    ) -> Optional[BaseAPIProvider]:
        """Get provider by type"""
        for provider in self.providers:
            if provider.config.provider_type == provider_type:
                return provider
        return None

    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        results = {}

        for index, provider in enumerate(self.providers):
            provider_key = provider.config.provider_type.value
            if provider.config.provider_type == APIProviderType.OLLAMA_REMOTE:
                base_url = provider.config.config.get("base_url") or getattr(
                    provider, "base_url", None
                )
                provider_key = f"{provider_key}:{base_url or index}"
            try:
                status = await provider.health_check()
                results[provider_key] = {
                    "status": status.value,
                    "metrics": provider.get_metrics(),
                }
            except Exception as e:
                results[provider_key] = {
                    "status": "error",
                    "error": str(e),
                }

        return results

    def get_available_providers(self) -> List[APIProviderType]:
        """Get list of currently available providers"""
        available = []
        for provider in self.providers:
            if provider.status == APIProviderStatus.HEALTHY:
                available.append(provider.config.provider_type)
        return available

    async def configure_thermal_integration(self, thermal_config: Dict[str, Any]):
        """Configure thermal management integration for local providers"""
        for provider in self.providers:
            if isinstance(provider, OllamaProvider) and provider.is_local:
                # Configure thermal monitoring for local Ollama instances
                provider.config.config["thermal_monitoring"] = thermal_config
                logger.info(
                    f"Configured thermal integration for {provider.config.provider_type.value}"
                )
