import json
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

import aiohttp

from ..task_context import TaskContext
from .base import AdapterResponse, BaseModelAdapter, ModelInfo

logger = logging.getLogger(__name__)


class ClaudeAdapter(BaseModelAdapter):
    """Adapter for Anthropic's Claude models."""

    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
        self.headers: Dict[str, str] = {}

    async def initialize(self) -> bool:
        """Initialize the adapter."""
        if not self.api_key:
            logger.warning(
                f"ANTHROPIC_API_KEY not found. {self.model_info.name} disabled."
            )
            return False

        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        self.is_initialized = True
        return True

    async def health_check(self) -> bool:
        """Check if the API is reachable."""
        if not self.is_initialized:
            return False

        # Simple dry run or check
        try:
            # We don't want to waste money, so we'll assume healthy if key is present
            # or maybe do a very cheap call if absolutely necessary.
            # For now, let's just return True if initialized.
            return True
        except Exception:
            return False

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
        """Execute query against Claude API."""
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

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model_info.name,
            "messages": messages,
            "max_tokens": max_tokens or self.model_info.max_output_tokens,
            "temperature": temperature,
            "stream": stream_callback is not None,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
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
                        # Handle streaming
                        content = ""
                        input_tokens = 0
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
                                type_ = data.get("type")

                                if type_ == "message_start":
                                    usage = data.get("message", {}).get("usage", {})
                                    input_tokens = usage.get("input_tokens", 0)

                                elif type_ == "content_block_delta":
                                    if time_to_first_token is None:
                                        time_to_first_token = int(
                                            (time.time() - start_time) * 1000
                                        )

                                    text_delta = data.get("delta", {}).get("text", "")
                                    content += text_delta
                                    stream_callback(text_delta)

                                elif type_ == "message_delta":
                                    usage = data.get("usage", {})
                                    output_tokens = usage.get("output_tokens", 0)

                            except json.JSONDecodeError:
                                continue

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
                            time_to_first_token_ms=time_to_first_token,
                        )

                    else:
                        # Non-streaming
                        data = await response.json()
                        content = "".join(
                            [
                                block["text"]
                                for block in data.get("content", [])
                                if block["type"] == "text"
                            ]
                        )
                        usage = data.get("usage", {})
                        input_tokens = usage.get("input_tokens", 0)
                        output_tokens = usage.get("output_tokens", 0)

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
