"""
Google Gemini Provider.
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


class GeminiProvider(BaseAPIProvider):
    """Google Gemini API provider."""

    def __init__(self, config: APIProviderConfig):
        # Enforce strict rate limits for free tier if not overridden
        if "rate_limit_rpm" not in config.config:
            config.config["rate_limit_rpm"] = 15
        if "rate_limit_rpd" not in config.config:
            config.config["rate_limit_rpd"] = 1500

        super().__init__(config)
        self.api_key = config.config.get("api_key") or os.getenv("GEMINI_API_KEY")
        self.base_url = config.config.get(
            "base_url", "https://generativelanguage.googleapis.com/v1beta"
        )
        self.model = config.config.get("model", "gemini-1.5-pro")

    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        """Execute query using Gemini API."""
        self.total_requests += 1
        start_time = time.time()

        try:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not configured")

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
                        if response.status == 429:
                            raise Exception("Rate limit exceeded (API 429)")
                        raise Exception(
                            f"Gemini API error {response.status}: {error_text}"
                        )

                    result = await response.json()

            if tools and tool_registry:
                parts = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [])
                )
                function_calls = [
                    part.get("functionCall")
                    for part in parts
                    if part.get("functionCall")
                ]
                if function_calls:
                    try:
                        from ...tool_registry import ToolExecutionContext
                    except ImportError:
                        from mycoder.tool_registry import ToolExecutionContext

                    tool_context = ToolExecutionContext(
                        mode=context.get("mode", "FULL") if context else "FULL",
                        working_directory=(
                            context.get("working_directory") if context else None
                        ),
                        session_id=context.get("session_id") if context else None,
                        thermal_status=(
                            context.get("thermal_status") if context else None
                        ),
                        network_status=(
                            context.get("network_status") if context else None
                        ),
                        resource_limits=(
                            context.get("resource_limits") if context else None
                        ),
                    )

                    followup_contents = [
                        {"role": "user", "parts": [{"text": full_prompt}]}
                    ]
                    for function_call in function_calls:
                        followup_contents.append(
                            {
                                "role": "model",
                                "parts": [{"functionCall": function_call}],
                            }
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
                # Sometimes safety filters block content
                prompt_feedback = result.get("promptFeedback", {})
                if prompt_feedback:
                    raise Exception(f"Blocked by safety filters: {prompt_feedback}")
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
        try:
            if not self.api_key:
                return APIProviderStatus.UNAVAILABLE

            # Simple list models check is lighter than generation
            url = f"{self.base_url}/models?key={self.api_key}"
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return APIProviderStatus.HEALTHY
                    return APIProviderStatus.DEGRADED
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return APIProviderStatus.UNAVAILABLE

    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        total_tokens = usage.get("totalTokenCount", 0)
        cost_per_token = 0.000001
        return total_tokens * cost_per_token
