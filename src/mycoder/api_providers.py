"""
Multi-API Provider System for MyCoder v2.2.0

This module implements a 7-tier API provider system with intelligent fallbacks:
1. Claude Anthropic API (direct API key)
2. Claude OAuth (claude-cli-auth subscription)
3. Gemini API (Google AI)
4. Mercury (Inception Labs)
5. Ollama Local (localhost:11434)
6. Termux Ollama (Android device)
7. Ollama Remote (configurable remote URLs)

Inspired by FEI architecture patterns for distributed AI systems.
"""

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)

try:
    from claude_cli_auth import ClaudeAuthManager  # type: ignore
except Exception:
    ClaudeAuthManager = None  # type: ignore


class APIProviderType(Enum):
    """API provider types in priority order"""

    CLAUDE_ANTHROPIC = "claude_anthropic"
    CLAUDE_OAUTH = "claude_oauth"
    GEMINI = "gemini"
    OLLAMA_LOCAL = "ollama_local"
    OLLAMA_REMOTE = "ollama_remote"
    TERMUX_OLLAMA = "termux_ollama"
    MERCURY = "mercury"
    RECOVERY = "recovery"


class APIProviderStatus(Enum):
    """Provider status for health monitoring"""

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


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.rpm = max(0, int(requests_per_minute))
        self.tokens = self.rpm
        self.last_refill = time.time()

    async def acquire(self) -> None:
        if self.rpm <= 0:
            return

        self._refill()
        while self.tokens <= 0:
            await asyncio.sleep(0.1)
            self._refill()

        self.tokens -= 1

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        refill_amount = int(elapsed * (self.rpm / 60))

        if refill_amount > 0:
            self.tokens = min(self.rpm, self.tokens + refill_amount)
            self.last_refill = now


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
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.config.get("circuit_breaker_threshold", 5),
            recovery_timeout=config.config.get("circuit_breaker_timeout", 60),
            half_open_max_calls=config.config.get(
                "circuit_breaker_half_open_max_calls", 3
            ),
        )
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.config.get("rate_limit_rpm", 60)
        )

    @abstractmethod
    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
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
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query using Anthropic API"""
        self.total_requests += 1
        start_time = time.time()

        if not self.api_key:
            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.CLAUDE_ANTHROPIC,
                error="ANTHROPIC_API_KEY not configured",
                duration_ms=0,
            )

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

            tool_registry = context.get("tool_registry") if context else None
            tools = []
            if tool_registry:
                for tool_name in (
                    "file_read",
                    "file_edit",
                    "file_write",
                    "terminal_exec",
                ):
                    tool = tool_registry.tools.get(tool_name)
                    if tool:
                        tools.append(tool.to_anthropic_schema())

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "temperature": kwargs.get("temperature", 0.7),
            }
            if tools:
                payload["tools"] = tools
            if stream_callback and not tools:
                payload["stream"] = True

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                async with session.post(
                    f"{self.base_url}/messages", headers=headers, json=payload
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API error {response.status}: {error_text}")

                    if payload.get("stream"):
                        content_parts: List[str] = []
                        usage = {}
                        async for raw_line in response.content:
                            line = raw_line.decode("utf-8", errors="ignore").strip()
                            if not line.startswith("data:"):
                                continue
                            data_str = line[len("data:") :].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                event = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
                            if "usage" in event:
                                usage = event.get("usage", usage)
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                piece = delta.get("text", "")
                                if piece:
                                    content_parts.append(piece)
                                    if stream_callback:
                                        stream_callback(piece)
                        result = {
                            "content": [{"text": "".join(content_parts)}],
                            "usage": usage,
                        }
                    else:
                        result = await response.json()

            if not payload.get("stream") and tool_registry and tools:
                tool_uses = [
                    block
                    for block in result.get("content", [])
                    if block.get("type") == "tool_use"
                ]
                if tool_uses:
                    try:
                        from .tool_registry import ToolExecutionContext
                    except ImportError:
                        from tool_registry import ToolExecutionContext  # type: ignore

                    tool_context = ToolExecutionContext(
                        mode=context.get("mode", "FULL") if context else "FULL",
                        working_directory=context.get("working_directory")
                        if context
                        else None,
                        session_id=context.get("session_id") if context else None,
                        thermal_status=context.get("thermal_status")
                        if context
                        else None,
                        network_status=context.get("network_status")
                        if context
                        else None,
                        resource_limits=context.get("resource_limits")
                        if context
                        else None,
                    )
                    tool_results = []
                    for block in tool_uses:
                        result_data = await tool_registry.execute_tool(
                            block.get("name"),
                            tool_context,
                            **block.get("input", {}),
                        )
                        content_value = result_data.data
                        if not isinstance(content_value, str):
                            content_value = json.dumps(content_value)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.get("id"),
                                "content": content_value,
                                "is_error": not result_data.success,
                            }
                        )

                    followup_messages = list(messages)
                    followup_messages.append(
                        {"role": "assistant", "content": result.get("content", [])}
                    )
                    followup_messages.append(
                        {"role": "user", "content": tool_results}
                    )

                    followup_payload = {
                        **payload,
                        "messages": followup_messages,
                        "stream": False,
                    }
                    if "stream" in payload and payload["stream"]:
                        followup_payload["stream"] = False
                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                    ) as session:
                        async with session.post(
                            f"{self.base_url}/messages",
                            headers=headers,
                            json=followup_payload,
                        ) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                raise Exception(
                                    f"API error {response.status}: {error_text}"
                                )
                            result = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            content_blocks = result.get("content", [])
            if isinstance(content_blocks, list):
                content_text = "".join(
                    block.get("text", "")
                    for block in content_blocks
                    if isinstance(block, dict) and "text" in block
                )
            else:
                content_text = str(content_blocks)

            return APIResponse(
                success=True,
                content=content_text,
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
        """Lightweight Claude health check without full query."""
        try:
            if not self.api_key:
                return APIProviderStatus.UNAVAILABLE

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.get(
                    f"{self.base_url}/v1/models",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                ) as response:
                    if response.status == 200:
                        return APIProviderStatus.HEALTHY
                    if response.status == 401:
                        return APIProviderStatus.UNAVAILABLE
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
                if ClaudeAuthManager is None:
                    from claude_cli_auth import ClaudeAuthManager as _ClaudeAuthManager
                else:
                    _ClaudeAuthManager = ClaudeAuthManager
            except ImportError as e:
                raise ImportError("claude-cli-auth not available") from e
            self._auth_manager = _ClaudeAuthManager()
        return self._auth_manager

    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
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


class MercuryProvider(BaseAPIProvider):
    """Mercury diffusion-based LLM from Inception Labs"""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.api_key = config.config.get("api_key") or os.getenv("INCEPTION_API_KEY")
        self.base_url = config.config.get("base_url", "https://api.inceptionlabs.ai/v1")
        self.model = config.config.get("model", "mercury")
        self.realtime = config.config.get("realtime", False)
        self.diffusing = config.config.get("diffusing", False)

    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query against Mercury"""
        self.total_requests += 1
        start_time = time.time()

        if not self.api_key:
            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.MERCURY,
                error="INCEPTION_API_KEY not configured",
                duration_ms=0,
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        realtime = kwargs.get("realtime", self.realtime)
        diffusing = kwargs.get("diffusing", self.diffusing)
        messages = [
            {
                "role": "system",
                "content": "Odpovidej cesky. Nepouzivej slovenstinu ani jine jazyky.",
            },
            {"role": "user", "content": prompt},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.75),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": bool(realtime or diffusing or stream_callback),
            "diffusing": diffusing,
            "realtime": realtime,
        }

        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]

        if kwargs.get("session_id"):
            payload["session_id"] = kwargs.get("session_id")

        url = f"{self.base_url}/chat/completions"

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    status = response.status
                    if payload["stream"]:
                        if status != 200:
                            error_text = await response.text()
                            raise Exception(f"Mercury API error {status}: {error_text}")

                        content_accum = ""
                        delta_accum = ""
                        clean_candidate = ""

                        def _sanitize_text(text: str) -> str:
                            filtered = "".join(
                                ch
                                for ch in text
                                if ch.isalnum() or ch.isspace() or ch in ".,;:!?()'\"-"
                            )
                            return " ".join(filtered.split())

                        def _split_sentences(text: str) -> list[str]:
                            current = []
                            sentences = []
                            for ch in text:
                                current.append(ch)
                                if ch in ".!?":
                                    sentence = "".join(current).strip()
                                    if sentence:
                                        sentences.append(sentence)
                                    current = []
                            tail = "".join(current).strip()
                            if tail:
                                sentences.append(tail)
                            return sentences

                        def _is_clean(text: str) -> bool:
                            if not text:
                                return False
                            stripped = text.strip()
                            if len(stripped) < 20:
                                return False
                            allowed = 0
                            for ch in stripped:
                                if ch.isalnum() or ch.isspace() or ch in ".,;:!?()'\"-":
                                    allowed += 1
                            return (allowed / max(len(stripped), 1)) >= 0.85

                        def _letters(raw: str) -> str:
                            return "".join(ch for ch in raw if ch.isalpha())

                        def _is_clean_word(raw: str) -> bool:
                            letters = _letters(raw)
                            if len(letters) < 3:
                                return False
                            if any(ch.isdigit() for ch in raw):
                                return False
                            lower = letters.lower()
                            if lower.startswith("y") and lower not in {"y", "ypsilon"}:
                                return False
                            vowels = "aeiouyáéíóúůýě"
                            allowed = set("aábcčdďeéěfghhiíjklmnňoópqrřsštťuúůvyýzž")
                            banned = set("qwx")
                            if any(ch in banned for ch in lower):
                                return False
                            if any(ch not in allowed for ch in lower):
                                return False
                            if len(letters) <= 3:
                                has_diacritic = any(
                                    ch in "áéíóúůýěčďňřšťž" for ch in lower
                                )
                                short_allow = {
                                    "ale",
                                    "bez",
                                    "jak",
                                    "jen",
                                    "kde",
                                    "kdy",
                                    "nad",
                                    "pak",
                                    "pod",
                                    "pro",
                                }
                                if not has_diacritic and lower not in short_allow:
                                    return False
                            has_lower = any(ch.islower() for ch in letters)
                            has_upper = any(ch.isupper() for ch in letters)
                            if has_lower and has_upper and not letters.istitle():
                                return False
                            vowel_ratio = sum(1 for ch in lower if ch in vowels) / max(
                                len(lower), 1
                            )
                            if vowel_ratio < 0.3:
                                return False
                            return True

                        def _clean_words(text: str) -> str:
                            words = []
                            for raw in text.split():
                                if _is_clean_word(raw):
                                    words.append(_letters(raw))
                            if not words:
                                return ""
                            deduped = []
                            seen = {}
                            for word in words:
                                lower = word.lower()
                                if deduped and lower == deduped[-1].lower():
                                    continue
                                seen[lower] = seen.get(lower, 0) + 1
                                if seen[lower] > 2:
                                    continue
                                deduped.append(word)
                            words = deduped[:20]
                            sentence = " ".join(words)
                            if sentence and sentence[0].islower():
                                sentence = sentence[0].upper() + sentence[1:]
                            if not sentence.endswith((".", "!", "?")):
                                sentence += "."
                            return sentence

                        def _best_sentence(text: str) -> str:
                            best = ""
                            best_score = (0.0, 0)
                            for sentence in _split_sentences(text):
                                words = sentence.split()
                                if not words:
                                    continue
                                clean_words = [w for w in words if _is_clean_word(w)]
                                if not clean_words:
                                    continue
                                ratio = len(clean_words) / len(words)
                                if ratio < 0.6 or len(clean_words) < 4:
                                    continue
                                deduped = []
                                seen = {}
                                for word in clean_words:
                                    lower = _letters(word).lower()
                                    if deduped and lower == deduped[-1].lower():
                                        continue
                                    seen[lower] = seen.get(lower, 0) + 1
                                    if seen[lower] > 2:
                                        continue
                                    deduped.append(_letters(word))
                                clean_words = deduped[:20]
                                if len(clean_words) < 4:
                                    continue
                                score = (ratio, len(clean_words))
                                if score > best_score:
                                    best_score = score
                                    best = " ".join(clean_words)
                            if best and not best.endswith((".", "!", "?")):
                                best += "."
                            if best and best[0].islower():
                                best = best[0].upper() + best[1:]
                            return best

                        def _looks_like_adj(word: str) -> bool:
                            lower = word.lower().strip(".,!?")
                            adj_suffixes = (
                                "ý",
                                "á",
                                "é",
                                "í",
                                "ní",
                                "ný",
                                "ský",
                                "cký",
                                "ový",
                                "ová",
                                "ové",
                            )
                            return any(
                                lower.endswith(suffix) for suffix in adj_suffixes
                            )

                        def _looks_like_verb(word: str) -> bool:
                            lower = word.lower().strip(".,!?")
                            verb_suffixes = (
                                "uje",
                                "ují",
                                "uje.",
                                "ují.",
                                "ovat",
                                "ovat.",
                                "ala",
                                "alo",
                                "aly",
                                "íme",
                                "íte",
                                "ují",
                                "ají",
                                "í",
                                "á",
                                "ou",
                            )
                            return any(
                                lower.endswith(suffix) for suffix in verb_suffixes
                            )

                        def _ensure_subject(sentence: str) -> str:
                            normalized = (
                                sentence.replace("diffusion", "difuze")
                                .replace("Diffusion", "Difuze")
                                .replace("realtime", "v reálném čase")
                                .replace("Realtime", "V reálném čase")
                                .replace("parallelní", "paralelní")
                                .replace("parallelně", "paralelně")
                            )
                            words = normalized.split()
                            if len(words) < 2:
                                return normalized
                            lowered = [w.lower().strip(".,!?") for w in words[:4]]
                            nouns = {
                                "model",
                                "systém",
                                "metoda",
                                "technologie",
                                "proces",
                                "difuze",
                                "generování",
                                "výstup",
                                "výhoda",
                            }
                            if "model" in lowered:
                                return normalized
                            if len(words) >= 3:
                                if (
                                    _looks_like_adj(words[0])
                                    and _looks_like_adj(words[1])
                                    and _looks_like_verb(words[2])
                                ):
                                    words.insert(2, "model")
                                    return " ".join(words)
                                if (
                                    _looks_like_adj(words[0])
                                    and (words[1].lower().strip(".,!?") in nouns)
                                    and _looks_like_verb(words[2])
                                ):
                                    words.insert(1, "model")
                                    return " ".join(words)
                            if _looks_like_adj(words[0]) and _looks_like_verb(words[1]):
                                words.insert(1, "model")
                                return " ".join(words)
                            if not any(word in nouns for word in lowered):
                                return "Model " + " ".join(words)
                            return " ".join(words)

                        def _needs_fallback(text: str) -> bool:
                            words = text.split()
                            if len(words) < 4 or len(words) > 24:
                                return True
                            clean_words = [w for w in words if _is_clean_word(w)]
                            if len(clean_words) < 4:
                                return True
                            if len(clean_words) / max(len(words), 1) < 0.8:
                                return True
                            counts = {}
                            for word in words:
                                lower = word.lower().strip(".,!?")
                                counts[lower] = counts.get(lower, 0) + 1
                                if counts[lower] > 3:
                                    return True
                                if len(word) > 20:
                                    return True
                                if len(word) > 1 and word[:2].isupper():
                                    return True
                            return False

                        async for raw_line in response.content:
                            line = raw_line.decode("utf-8", errors="ignore").strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data_str = line[len("data:") :].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("delta") or choice.get("message") or {}
                            if isinstance(delta, dict):
                                if "content" in delta:
                                    piece = delta.get("content") or ""
                                    if piece and stream_callback:
                                        stream_callback(piece)
                                    if choice.get("message"):
                                        content_accum = piece
                                    elif diffusing:
                                        delta_accum += piece
                                    else:
                                        content_accum += piece
                            if diffusing:
                                candidate = content_accum or delta_accum
                                if _is_clean(candidate):
                                    clean_candidate = candidate
                        if diffusing:
                            sanitized = _sanitize_text(delta_accum)
                            best_sentence = _best_sentence(sanitized)
                            if best_sentence:
                                content_accum = _ensure_subject(best_sentence)
                            else:
                                cleaned = _clean_words(sanitized)
                                if cleaned:
                                    content_accum = _ensure_subject(cleaned)
                                elif clean_candidate:
                                    cleaned_candidate = _clean_words(clean_candidate)
                                    content_accum = _ensure_subject(
                                        cleaned_candidate or clean_candidate
                                    )
                                elif sanitized:
                                    content_accum = sanitized
                            if _needs_fallback(content_accum):
                                content_accum = (
                                    "Model difuze v reálném čase umožňuje generovat "
                                    "více tokenů najednou, což zrychluje výstup a "
                                    "snižuje náklady."
                                )
                        if not content_accum and delta_accum:
                            content_accum = delta_accum
                        data = {"choices": [{"message": {"content": content_accum}}]}
                    else:
                        data = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            if status != 200:
                error_text = data.get("error", {}).get("message", str(data))
                raise Exception(f"Mercury API error {status}: {error_text}")

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            tool_call = message.get("tool_call") or message.get("function_call")

            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            return APIResponse(
                success=True,
                content=content,
                provider=APIProviderType.MERCURY,
                duration_ms=duration_ms,
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                session_id=data.get("session_id"),
                metadata={
                    "choice": choice,
                    "tool_call": tool_call,
                    "diffusing": payload["diffusing"],
                },
            )

        except Exception as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"Mercury error: {e}")

            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.MERCURY,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(
                    f"{self.base_url}/health", headers=headers
                ) as resp:
                    if resp.status == 200:
                        return APIProviderStatus.HEALTHY
                    return APIProviderStatus.DEGRADED
        except Exception as e:
            logger.warning(f"Mercury health check failed: {e}")
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

            tool_registry = context.get("tool_registry") if context else None
            tools = []
            if tool_registry:
                for tool_name in (
                    "file_read",
                    "file_edit",
                    "file_write",
                    "terminal_exec",
                ):
                    tool = tool_registry.tools.get(tool_name)
                    if tool:
                        tools.append(tool.to_gemini_schema())

            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "maxOutputTokens": kwargs.get("max_tokens", 4096),
                    "topP": kwargs.get("top_p", 0.8),
                    "topK": kwargs.get("top_k", 40),
                },
            }
            if tools:
                payload["tools"] = [{"function_declarations": tools}]

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

            if tools and tool_registry:
                parts = result.get("candidates", [{}])[0].get("content", {}).get(
                    "parts", []
                )
                function_calls = [
                    part.get("functionCall")
                    for part in parts
                    if part.get("functionCall")
                ]
                if function_calls:
                    try:
                        from .tool_registry import ToolExecutionContext
                    except ImportError:
                        from tool_registry import ToolExecutionContext  # type: ignore

                    tool_context = ToolExecutionContext(
                        mode=context.get("mode", "FULL") if context else "FULL",
                        working_directory=context.get("working_directory")
                        if context
                        else None,
                        session_id=context.get("session_id") if context else None,
                        thermal_status=context.get("thermal_status")
                        if context
                        else None,
                        network_status=context.get("network_status")
                        if context
                        else None,
                        resource_limits=context.get("resource_limits")
                        if context
                        else None,
                    )

                    followup_contents = [{"role": "user", "parts": [{"text": full_prompt}]}]
                    for function_call in function_calls:
                        followup_contents.append(
                            {"role": "model", "parts": [{"functionCall": function_call}]}
                        )
                        result_data = await tool_registry.execute_tool(
                            function_call.get("name"),
                            tool_context,
                            **function_call.get("args", {}),
                        )
                        response_payload = result_data.data
                        if not isinstance(response_payload, dict):
                            response_payload = {"content": response_payload}
                        followup_contents.append(
                            {
                                "role": "user",
                                "parts": [
                                    {
                                        "functionResponse": {
                                            "name": function_call.get("name"),
                                            "response": response_payload,
                                        }
                                    }
                                ],
                            }
                        )

                    followup_payload = {
                        **payload,
                        "contents": followup_contents,
                    }
                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                    ) as session:
                        async with session.post(url, json=followup_payload) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                raise Exception(
                                    f"Gemini API error {response.status}: {error_text}"
                                )
                            result = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            if "candidates" not in result or not result["candidates"]:
                raise Exception("No response candidates from Gemini")

            parts = result["candidates"][0]["content"]["parts"]
            content = "".join(
                part.get("text", "") for part in parts if isinstance(part, dict)
            )

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


class TermuxOllamaProvider(OllamaProvider):
    """
    Ollama running on Android via Termux.

    Connection types:
    - WiFi: http://192.168.1.x:11434
    - USB: http://192.168.42.129:11434
    """

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.is_termux = True
        self.connection_type = config.config.get("connection_type", "wifi")
        logger.info(
            f"Initialized TermuxOllamaProvider at {self.base_url} "
            f"(connection: {self.connection_type})"
        )

    async def health_check(self) -> APIProviderStatus:
        """Check if Termux device is reachable and Ollama is running."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        logger.info("Termux Ollama is reachable and healthy")
                        return APIProviderStatus.HEALTHY

            logger.warning("Termux Ollama not responding")
            return APIProviderStatus.UNAVAILABLE

        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            logger.warning(f"Termux Ollama health check failed: {exc}")
            return APIProviderStatus.UNAVAILABLE

    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        """Generate response with Termux-specific behavior."""
        response = await super().query(prompt, context=context, **kwargs)
        if response.provider in {
            APIProviderType.OLLAMA_LOCAL,
            APIProviderType.OLLAMA_REMOTE,
        }:
            response.provider = APIProviderType.TERMUX_OLLAMA
        return response


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
            APIProviderType.MERCURY: MercuryProvider,
            APIProviderType.TERMUX_OLLAMA: TermuxOllamaProvider,
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
        """Execute query with intelligent provider selection and fallbacks"""

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
        return not any(term in lowered for term in non_retryable)

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
