"""
Multi-API Provider System for MyCoder v2.2.0

This module is now a compatibility facade for the new modular provider system.
See `src/mycoder/providers/` for implementation details.
"""

import aiohttp

from .providers.base import (
    APIProviderType,
    APIProviderStatus,
    CircuitState,
    CircuitBreaker,
    APIResponse,
    APIProviderConfig,
    BaseAPIProvider,
)
from .providers.router import APIProviderRouter
from .providers.llm import (
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
    HuggingFaceProvider,
)

# Export legacy names or any other utilities if needed
# The router is the main component used by the rest of the app

try:
    from claude_cli_auth import ClaudeAuthManager  # type: ignore
except Exception:
    ClaudeAuthManager = None  # type: ignore

__all__ = [
    "ClaudeAuthManager",
    "APIProviderType",
    "APIProviderStatus",
    "CircuitState",
    "CircuitBreaker",
    "APIResponse",
    "APIProviderConfig",
    "BaseAPIProvider",
    "APIProviderRouter",
    "ClaudeAnthropicProvider",
    "ClaudeOAuthProvider",
    "GeminiProvider",
    "OllamaProvider",
    "TermuxOllamaProvider",
    "MercuryProvider",
    "BedrockProvider",
    "OpenAIProvider",
    "XAIProvider",
    "MistralProvider",
    "HuggingFaceProvider",
]
