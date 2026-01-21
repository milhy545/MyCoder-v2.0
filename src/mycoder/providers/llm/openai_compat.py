"""
OpenAI Compatible Providers (OpenAI, X.AI, etc.).
"""

import logging
import os
import time
import aiohttp
from typing import Any, Callable, Dict, List, Optional

from ..base import (
    BaseAPIProvider,
    APIResponse,
    APIProviderType,
    APIProviderStatus,
    APIProviderConfig
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAPIProvider):
    """Standard OpenAI API Provider."""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.api_key = config.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.base_url = config.config.get("base_url", "https://api.openai.com/v1")
        self.model = config.config.get("model", "gpt-4o")

    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query using OpenAI API."""
        self.total_requests += 1
        start_time = time.time()

        if not self.api_key:
            return APIResponse(
                success=False,
                content="",
                provider=self.config.provider_type,
                error="API Key not configured",
                duration_ms=0,
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
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
            "stream": bool(stream_callback),
        }

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API error {response.status}: {error_text}")

                    if payload["stream"]:
                        content_accum = ""
                        async for raw_line in response.content:
                            line = raw_line.decode("utf-8", errors="ignore").strip()
                            if not line.startswith("data:"):
                                continue
                            data_str = line[len("data:") :].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    content_accum += content
                                    if stream_callback:
                                        stream_callback(content)
                            except Exception:
                                continue

                        # Construct a mock result for the end
                        result = {
                            "choices": [{"message": {"content": content_accum}}],
                            "usage": {"total_tokens": 0} # Usage often not sent in stream
                        }
                    else:
                        result = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)
            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            return APIResponse(
                success=True,
                content=content,
                provider=self.config.provider_type,
                cost=0.0,
                duration_ms=duration_ms,
                tokens_used=usage.get("total_tokens", 0),
                session_id=kwargs.get("session_id"),
                metadata={
                    "model": self.model,
                    "usage": usage,
                },
            )

        except Exception as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"{self.config.provider_type.value} error: {e}")

            return APIResponse(
                success=False,
                content="",
                provider=self.config.provider_type,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        try:
             if not self.api_key:
                return APIProviderStatus.UNAVAILABLE

             headers = {"Authorization": f"Bearer {self.api_key}"}
             async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                 async with session.get(f"{self.base_url}/models", headers=headers) as response:
                     if response.status == 200:
                         return APIProviderStatus.HEALTHY
                     return APIProviderStatus.DEGRADED
        except Exception:
            return APIProviderStatus.UNAVAILABLE


class XAIProvider(OpenAIProvider):
    """X.AI (Grok) Provider."""

    def __init__(self, config: APIProviderConfig):
        # Override defaults for X.AI
        if "base_url" not in config.config:
            config.config["base_url"] = "https://api.x.ai/v1"
        if "model" not in config.config:
            config.config["model"] = "grok-beta"
        if "api_key" not in config.config and not os.getenv("XAI_API_KEY"):
            # Fallback to specific env var if generic not set
             pass

        super().__init__(config)
        # Re-check API key from specific env var
        self.api_key = config.config.get("api_key") or os.getenv("XAI_API_KEY")
