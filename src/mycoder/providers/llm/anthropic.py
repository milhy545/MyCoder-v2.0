"""
Anthropic Claude Providers.
"""

import json
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

try:
    from claude_cli_auth import ClaudeAuthManager  # type: ignore
except Exception:
    ClaudeAuthManager = None  # type: ignore


class ClaudeAnthropicProvider(BaseAPIProvider):
    """Claude API provider using direct Anthropic API."""

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
        """Execute query using Anthropic API."""
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

            # Handle tools if present
            if not payload.get("stream") and tool_registry and tools:
                tool_uses = [
                    block
                    for block in result.get("content", [])
                    if block.get("type") == "tool_use"
                ]
                if tool_uses:
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
                    followup_messages.append({"role": "user", "content": tool_results})

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

            duration_ms = getattr(response, "duration_ms", None)
            if duration_ms is None:
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
        """Lightweight Claude health check."""
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

    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        # Claude 3.5 Sonnet pricing
        input_cost_per_token = 0.000003
        output_cost_per_token = 0.000015
        return (input_tokens * input_cost_per_token) + (
            output_tokens * output_cost_per_token
        )


class ClaudeOAuthProvider(BaseAPIProvider):
    """Claude provider using claude-cli-auth OAuth."""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self._auth_manager = None

    async def _get_auth_manager(self):
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
        """Execute query using Claude OAuth."""
        self.total_requests += 1
        start_time = time.time()

        try:
            auth_manager = await self._get_auth_manager()
            auth_kwargs = {"timeout": self.config.timeout_seconds}

            if context:
                if context.get("working_directory"):
                    auth_kwargs["working_directory"] = context["working_directory"]
                if context.get("files"):
                    auth_kwargs["files"] = [str(f) for f in context["files"]]

            if kwargs.get("session_id"):
                auth_kwargs["session_id"] = kwargs["session_id"]
                auth_kwargs["continue_session"] = kwargs.get("continue_session", False)

            response = await auth_manager.query(prompt, **auth_kwargs)

            duration_ms = int((time.time() - start_time) * 1000)
            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            return APIResponse(
                success=True,
                content=response.content,
                provider=APIProviderType.CLAUDE_OAUTH,
                cost=response.cost,
                duration_ms=duration_ms,
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
        try:
            auth_manager = await self._get_auth_manager()
            test_response = await auth_manager.query("Hello", timeout=10)
            if hasattr(test_response, "content") and test_response.content:
                return APIProviderStatus.HEALTHY
            else:
                return APIProviderStatus.DEGRADED
        except Exception as e:
            logger.warning(f"Claude OAuth health check failed: {e}")
            return APIProviderStatus.UNAVAILABLE
