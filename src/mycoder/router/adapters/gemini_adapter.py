import logging
import os
import time
from typing import Any, Callable, Optional

import aiohttp

from ..task_context import TaskContext
from .base import AdapterResponse, BaseModelAdapter, ModelInfo

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseModelAdapter):
    """Adapter for Google Gemini models."""

    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def initialize(self) -> bool:
        """Initialize the adapter."""
        if not self.api_key:
            logger.warning(
                f"GEMINI_API_KEY not found. {self.model_info.name} disabled."
            )
            return False
        self.is_initialized = True
        return True

    async def health_check(self) -> bool:
        """Check if the API is reachable."""
        return self.is_initialized

    async def query(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[TaskContext] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AdapterResponse:
        """Execute query against Gemini API."""
        if not self.is_initialized:
            return AdapterResponse(
                success=False,
                content="",
                model_name=self.model_info.name,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                duration_ms=0,
                error="Adapter not initialized",
            )

        start_time = time.time()

        # Gemini structure
        contents = [{"parts": [{"text": prompt}]}]
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens or self.model_info.max_output_tokens,
                "temperature": temperature,
            },
        }

        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

        # Use non-streaming endpoint; if streaming is requested, we emit the full
        # response as a single callback to keep behavior deterministic.
        method = "generateContent"
        url = f"{self.base_url}/{self.model_info.name}:{method}?key={self.api_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return AdapterResponse(
                            success=False,
                            content="",
                            model_name=self.model_info.name,
                            input_tokens=0,
                            output_tokens=0,
                            cost_usd=0.0,
                            duration_ms=int((time.time() - start_time) * 1000),
                            error=f"API Error {response.status}: {error_text}",
                        )

                    # NON-STREAMING (simpler to implement raw)
                    data = await response.json()

                    # Extract text
                    text_parts = []
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text_parts.append(part.get("text", ""))

                    content = "".join(text_parts)

                    # Usage
                    usage_meta = data.get("usageMetadata", {})
                    input_tokens = usage_meta.get("promptTokenCount", 0)
                    output_tokens = usage_meta.get("candidatesTokenCount", 0)

                    duration_ms = int((time.time() - start_time) * 1000)
                    cost = self.estimate_cost(input_tokens, output_tokens)

                    if stream_callback:
                        stream_callback(content)  # Burst stream

                    return AdapterResponse(
                        success=True,
                        content=content,
                        model_name=self.model_info.name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_usd=cost,
                        duration_ms=duration_ms,
                    )

        except Exception as e:
            return AdapterResponse(
                success=False,
                content="",
                model_name=self.model_info.name,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )
