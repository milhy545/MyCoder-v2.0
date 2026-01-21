"""
Ollama Provider.
"""

import asyncio
import logging
import os
import subprocess
import time
from typing import Any, Dict

import aiohttp

from ..base import (
    APIProviderConfig,
    APIProviderStatus,
    APIProviderType,
    APIResponse,
    BaseAPIProvider,
)

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAPIProvider):
    """Ollama provider for local and remote instances."""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.base_url = config.config.get("base_url", "http://localhost:11434")
        self.model = config.config.get("model", "tinyllama")
        self.is_local = "localhost" in self.base_url or "127.0.0.1" in self.base_url
        self.is_termux = config.provider_type == APIProviderType.TERMUX_OLLAMA

    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        """Execute query using Ollama."""
        self.total_requests += 1
        start_time = time.time()

        try:
            full_prompt = prompt
            if context and context.get("files"):
                file_content = await self._process_file_context(
                    context["files"], max_files=3, max_chars=2000
                )
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

            if self.is_local and context and context.get("thermal_monitoring"):
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

            # Determine correct provider type for response
            provider_type = self.config.provider_type

            return APIResponse(
                success=True,
                content=result.get("response", ""),
                provider=provider_type,
                cost=0.0,
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

            return APIResponse(
                success=False,
                content="",
                provider=self.config.provider_type,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        """Check Ollama instance health."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                # Check /api/tags or /api/version
                endpoint = "/api/tags" if self.is_termux else "/api/version"
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        return APIProviderStatus.HEALTHY
                    else:
                        return APIProviderStatus.DEGRADED

        except Exception as e:
            logger.warning(f"Ollama health check failed ({self.base_url}): {e}")
            return APIProviderStatus.UNAVAILABLE

    async def _check_thermal_status(self) -> Dict[str, Any]:
        """Check thermal status for local instances."""
        try:
            thermal_script = os.environ.get("MYCODER_THERMAL_SCRIPT", "")
            if not thermal_script or not os.path.exists(thermal_script):
                return {"should_throttle": False}

            result = subprocess.run(
                [thermal_script, "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
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
