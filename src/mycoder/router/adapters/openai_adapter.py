import json
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

import aiohttp

from ..task_context import TaskContext
from .base import AdapterResponse, BaseModelAdapter, ModelInfo

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI models (GPT-4o, etc.)."""

    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        self.headers: Dict[str, str] = {}

    async def initialize(self) -> bool:
        """Initialize the adapter."""
        if not self.api_key:
            logger.warning(
                f"OPENAI_API_KEY not found. {self.model_info.name} disabled."
            )
            return False

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
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
        """Execute query against OpenAI API."""
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

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_info.name,
            "messages": messages,
            "max_tokens": max_tokens or self.model_info.max_output_tokens,
            "temperature": temperature,
            "stream": stream_callback is not None,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                ) as response:
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

                    if stream_callback:
                        content = ""
                        input_tokens = 0  # OpenAI stream doesn't always send usage
                        output_tokens = 0
                        time_to_first_token = None

                        async for line in response.content:
                            line_text = line.decode("utf-8").strip()
                            if not line_text.startswith("data: "):
                                continue

                            data_str = line_text[6:]
                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if not choices:
                                    continue

                                delta = choices[0].get("delta", {})
                                content_delta = delta.get("content", "")

                                if content_delta:
                                    if time_to_first_token is None:
                                        time_to_first_token = int(
                                            (time.time() - start_time) * 1000
                                        )
                                    content += content_delta
                                    stream_callback(content_delta)

                                # Some models/options might send usage in stream now
                                if data.get("usage"):
                                    input_tokens = data["usage"].get("prompt_tokens", 0)
                                    output_tokens = data["usage"].get(
                                        "completion_tokens", 0
                                    )

                            except json.JSONDecodeError:
                                continue

                        duration_ms = int((time.time() - start_time) * 1000)

                        # Estimate usage if not provided
                        if input_tokens == 0:
                            input_tokens = len(prompt) // 4  # Rough estimate
                            output_tokens = len(content) // 4

                        cost = self.estimate_cost(input_tokens, output_tokens)

                        return AdapterResponse(
                            success=True,
                            content=content,
                            model_name=self.model_info.name,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            cost_usd=cost,
                            duration_ms=duration_ms,
                            time_to_first_token_ms=time_to_first_token,
                        )
                    else:
                        data = await response.json()
                        choice = data["choices"][0]
                        content = choice["message"]["content"]

                        usage = data.get("usage", {})
                        input_tokens = usage.get("prompt_tokens", 0)
                        output_tokens = usage.get("completion_tokens", 0)

                        duration_ms = int((time.time() - start_time) * 1000)
                        cost = self.estimate_cost(input_tokens, output_tokens)

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
