"""
Hugging Face Inference API Provider.
"""

import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional

import aiohttp

from ..base import (
    APIProviderConfig,
    APIProviderStatus,
    APIProviderType,
    APIResponse,
    BaseAPIProvider,
)

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseAPIProvider):
    """Hugging Face Inference API Provider."""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.api_key = config.config.get("api_key") or os.getenv("HF_TOKEN")
        self.base_url = config.config.get(
            "base_url", "https://api-inference.huggingface.co/models"
        )
        # Default to a popular open model
        self.model = config.config.get("model", "meta-llama/Llama-3.2-3B-Instruct")

    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query using HF Inference API."""
        self.total_requests += 1
        start_time = time.time()

        if not self.api_key:
            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.HUGGINGFACE,
                error="HF_TOKEN not configured",
                duration_ms=0,
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # HF Inference API typically uses a simple payload
        # For "Conversational" or "Text Generation"
        # We'll use text-generation format.

        full_prompt = prompt
        if context and context.get("files"):
            file_content = await self._process_file_context(context["files"])
            if file_content:
                full_prompt = f"{file_content}\n\n{prompt}"

        # Some models require specific templating, but for raw API we often send raw text
        # unless using TGI/v1/chat/completions endpoint.
        # The standard inference API is raw generation.

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "return_full_text": False,
            },
        }

        url = f"{self.base_url}/{self.model}"

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                async with session.post(url, headers=headers, json=payload) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        # Handle model loading state
                        if "currently loading" in error_text.lower():
                            # Wait and retry logic handled by caller/circuit breaker ideally,
                            # but here we just report error
                            pass
                        raise Exception(f"HF API error {response.status}: {error_text}")

                    result = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)
            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            # Result format depends on task. For text-generation it's usually list of dicts.
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get("generated_text", "")
            else:
                content = str(result)

            return APIResponse(
                success=True,
                content=content,
                provider=APIProviderType.HUGGINGFACE,
                cost=0.0,
                duration_ms=duration_ms,
                tokens_used=0,  # Not provided by standard inference API usually
                session_id=kwargs.get("session_id"),
                metadata={
                    "model": self.model,
                },
            )

        except Exception as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"HuggingFace error: {e}")

            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.HUGGINGFACE,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        # Check if model exists/is accessible
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            # Lightweight call to model info? Or just a simple generation with max_tokens=1
            url = f"{self.base_url}/{self.model}"
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                # Sending empty inputs usually triggers error but validates auth/availability
                async with session.post(
                    url, headers=headers, json={"inputs": "test"}
                ) as response:
                    if (
                        response.status == 200 or response.status == 503
                    ):  # 503 means loading, which implies reachable
                        return APIProviderStatus.HEALTHY
                    return APIProviderStatus.UNAVAILABLE
        except Exception:
            return APIProviderStatus.UNAVAILABLE
