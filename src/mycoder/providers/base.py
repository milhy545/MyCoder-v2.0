"""
Base API Provider Classes.
Defines the standard interface for all AI providers in MyCoder.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .rate_limiter import PersistentRateLimiter

logger = logging.getLogger(__name__)


class APIProviderType(Enum):
    """API provider types in priority order."""

    # LLM Providers
    CLAUDE_ANTHROPIC = "claude_anthropic"
    CLAUDE_OAUTH = "claude_oauth"
    GEMINI = "gemini"
    OLLAMA_LOCAL = "ollama_local"
    OLLAMA_REMOTE = "ollama_remote"
    TERMUX_OLLAMA = "termux_ollama"
    MERCURY = "mercury"
    AWS_BEDROCK = "aws_bedrock"
    OPENAI = "openai"
    X_AI = "x_ai"
    MISTRAL = "mistral"
    HUGGINGFACE = "huggingface"

    # Fallback/System
    RECOVERY = "recovery"


class APIProviderStatus(Enum):
    """Provider status for health monitoring."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        return self.half_open_calls < self.half_open_max_calls

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


@dataclass
class APIResponse:
    """Standardized API response across all providers."""

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
    """Configuration for API providers."""

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
    """Base class for all API providers with FEI-inspired patterns."""

    def __init__(self, config: APIProviderConfig):
        self.config = config
        self.status = APIProviderStatus.UNKNOWN
        self.last_health_check = 0
        self.error_count = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.config.get("circuit_breaker_threshold", 5),
            recovery_timeout=config.config.get("circuit_breaker_timeout", 60),
            half_open_max_calls=config.config.get(
                "circuit_breaker_half_open_max_calls", 3
            ),
        )

        # Initialize persistent rate limiter
        self.rate_limiter = PersistentRateLimiter(
            provider_id=config.provider_type.value,
            rpm=config.config.get("rate_limit_rpm", 60),
            rpd=config.config.get("rate_limit_rpd", 1500),  # Default 1500 RPD
        )

    @abstractmethod
    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query with provider-specific implementation."""
        pass

    @abstractmethod
    async def health_check(self) -> APIProviderStatus:
        """Check provider health and availability."""
        pass

    async def can_handle_request(self, context: Dict[str, Any] = None) -> bool:
        """Check if provider can handle the request."""
        if not self.config.enabled:
            return False
        if not self.circuit_breaker.can_execute():
            logger.info(f"Circuit breaker OPEN for {self.config.provider_type.value}")
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
        """Get provider performance metrics."""
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

    async def _process_file_context(
        self, files: List[Path], max_files: int = 5, max_chars: int = 8000
    ) -> str:
        """Process file context for APIs."""
        file_contents = []
        for file_path in files[:max_files]:
            try:
                if file_path.exists() and file_path.is_file():
                    content = file_path.read_text(encoding="utf-8")[:max_chars]
                    file_contents.append(f"File: {file_path.name}\n```\n{content}\n```")
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")

        return "\n\n".join(file_contents) if file_contents else ""
