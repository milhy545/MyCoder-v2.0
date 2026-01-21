"""
API Provider Router.
Manages selection and fallback for multiple AI providers.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from .base import (
    BaseAPIProvider,
    APIResponse,
    APIProviderType,
    APIProviderStatus,
    APIProviderConfig
)
from .llm import (
    ClaudeAnthropicProvider,
    ClaudeOAuthProvider,
    GeminiProvider,
    OllamaProvider,
    TermuxOllamaProvider,
    MercuryProvider,
    BedrockProvider,
    OpenAIProvider,
    XAIProvider,
    MistralProvider,
    HuggingFaceProvider
)

logger = logging.getLogger(__name__)


class APIProviderRouter:
    """Router for managing multiple API providers with fallback logic."""

    def __init__(self, configs: List[APIProviderConfig]):
        self.providers: List[BaseAPIProvider] = []
        self.fallback_chain: List[APIProviderType] = []
        self._initialize_providers(configs)

    def _initialize_providers(self, configs: List[APIProviderConfig]):
        """Initialize all configured providers."""
        provider_classes = {
            APIProviderType.CLAUDE_ANTHROPIC: ClaudeAnthropicProvider,
            APIProviderType.CLAUDE_OAUTH: ClaudeOAuthProvider,
            APIProviderType.GEMINI: GeminiProvider,
            APIProviderType.OLLAMA_LOCAL: OllamaProvider,
            APIProviderType.OLLAMA_REMOTE: OllamaProvider,
            APIProviderType.TERMUX_OLLAMA: TermuxOllamaProvider,
            APIProviderType.MERCURY: MercuryProvider,
            APIProviderType.AWS_BEDROCK: BedrockProvider,
            APIProviderType.OPENAI: OpenAIProvider,
            APIProviderType.X_AI: XAIProvider,
            APIProviderType.MISTRAL: MistralProvider,
            APIProviderType.HUGGINGFACE: HuggingFaceProvider,
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
        fallback_enabled: bool = True,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query with intelligent provider selection and fallbacks."""

        # Determine provider order
        provider_order = []

        if preferred_provider and preferred_provider in self.fallback_chain:
            provider_order.append(preferred_provider)
            if fallback_enabled:
                provider_order.extend(
                    [p for p in self.fallback_chain if p != preferred_provider]
                )
        else:
            if fallback_enabled:
                provider_order = self.fallback_chain.copy()
            elif self.fallback_chain:
                provider_order = [self.fallback_chain[0]]

        logger.info(f"Query execution order: {[p.value for p in provider_order]}")

        last_error = None
        attempted_providers: List[str] = []
        attempted_errors: Dict[str, str] = {}

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

                attempts = max(1, provider.config.max_retries)
                for attempt in range(1, attempts + 1):
                    logger.info(
                        f"Attempting query with {provider_type.value} (attempt {attempt}/{attempts})"
                    )
                    if getattr(provider, "rate_limiter", None):
                        await provider.rate_limiter.acquire()

                    response = await provider.query(
                        prompt,
                        context,
                        stream_callback=stream_callback,
                        **kwargs,
                    )
                    if provider_type.value not in attempted_providers:
                        attempted_providers.append(provider_type.value)

                    if response.success:
                        provider.circuit_breaker.record_success()
                        logger.info(f"Query successful with {provider_type.value}")
                        if response.metadata is None:
                            response.metadata = {}
                        response.metadata.setdefault(
                            "attempted_providers", attempted_providers
                        )
                        response.metadata.setdefault(
                            "attempted_errors", attempted_errors
                        )
                        response.metadata.setdefault(
                            "fallback_used", len(attempted_providers) > 1
                        )
                        return response

                    provider.circuit_breaker.record_failure()
                    logger.warning(
                        f"Provider {provider_type.value} returned error: {response.error}"
                    )
                    last_error = response.error
                    attempted_errors[provider_type.value] = response.error or "unknown"
                    if not self._is_retryable_error(response.error):
                        break

            except Exception as e:
                provider.circuit_breaker.record_failure()
                logger.error(f"Provider {provider_type.value} failed: {e}")
                last_error = str(e)
                attempted_errors[provider_type.value] = last_error
                continue

        # All providers failed
        logger.error("All API providers failed")
        return APIResponse(
            success=False,
            content="",
            provider=APIProviderType.RECOVERY,
            error=f"All providers failed. Last error: {last_error}",
            metadata={
                "attempted_providers": attempted_providers
                or [p.value for p in provider_order],
                "attempted_errors": attempted_errors,
                "fallback_used": len(attempted_providers) > 1,
            },
        )

    @staticmethod
    def _is_retryable_error(error: Optional[str]) -> bool:
        if not error:
            return True
        lowered = error.lower()
        non_retryable = (
            "invalid api key",
            "authentication failed",
            "unauthorized",
            "api quota",
            "quota exceeded",
            "permission",
            "rate limit",
        )
        # Exception: API rate limit (429) IS retryable in circuit breaker context if we have fallbacks,
        # but locally we might want to stop hammering.
        # Actually "rate limit" is in non_retryable list above.
        # If one provider is rate limited, we SHOULD fail over to next provider.
        # So "non-retryable" here means "don't retry SAME provider".
        # But we loop over providers.
        # The loop breaks if `_is_retryable_error` returns False.
        # So if we get "rate limit", we break loop? No, we should continue to next provider.
        # The logic `if not self._is_retryable_error(response.error): break` is inside the ATTEMPT loop (retries for same provider).
        # So breaking here means "stop trying this provider".
        # Then the outer loop continues to next provider. Correct.
        return not any(term in lowered for term in non_retryable)

    def _get_provider(
        self, provider_type: APIProviderType
    ) -> Optional[BaseAPIProvider]:
        """Get provider by type."""
        for provider in self.providers:
            if provider.config.provider_type == provider_type:
                return provider
        return None

    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all providers."""
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
        """Get list of currently available providers."""
        available = []
        for provider in self.providers:
            if provider.status == APIProviderStatus.HEALTHY:
                available.append(provider.config.provider_type)
        return available

    async def configure_thermal_integration(self, thermal_config: Dict[str, Any]):
        """Configure thermal management integration for local providers."""
        for provider in self.providers:
            if isinstance(provider, OllamaProvider) and provider.is_local:
                # Configure thermal monitoring for local Ollama instances
                provider.config.config["thermal_monitoring"] = thermal_config
                logger.info(
                    f"Configured thermal integration for {provider.config.provider_type.value}"
                )
