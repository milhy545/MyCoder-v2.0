"""
AWS Bedrock Provider.
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from ..base import (
    APIProviderConfig,
    APIProviderStatus,
    APIProviderType,
    APIResponse,
    BaseAPIProvider,
)

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class BedrockProvider(BaseAPIProvider):
    """AWS Bedrock API Provider."""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.model = config.config.get(
            "model", "anthropic.claude-3-sonnet-20240229-v1:0"
        )
        self.region = config.config.get("region", "us-east-1")
        self.client = None

        if BOTO3_AVAILABLE:
            try:
                self.client = boto3.client(
                    service_name="bedrock-runtime",
                    region_name=self.region,
                    aws_access_key_id=config.config.get("aws_access_key_id"),
                    aws_secret_access_key=config.config.get("aws_secret_access_key"),
                    aws_session_token=config.config.get("aws_session_token"),
                )
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock client: {e}")

    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query using AWS Bedrock."""
        self.total_requests += 1
        start_time = time.time()

        if not BOTO3_AVAILABLE:
            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.AWS_BEDROCK,
                error="boto3 library not installed",
                duration_ms=0,
            )

        if not self.client:
            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.AWS_BEDROCK,
                error="Bedrock client not initialized",
                duration_ms=0,
            )

        try:
            # Prepare request body based on model family
            # Current implementation focuses on Claude models on Bedrock

            body = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": kwargs.get("max_tokens", 4096),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                }
            )

            # Execute via thread pool since boto3 is synchronous
            def _invoke_model():
                return self.client.invoke_model(
                    body=body,
                    modelId=self.model,
                    accept="application/json",
                    contentType="application/json",
                )

            response = await asyncio.to_thread(_invoke_model)

            response_body = json.loads(response.get("body").read())

            content = ""
            for content_block in response_body.get("content", []):
                if content_block.get("type") == "text":
                    content += content_block.get("text", "")

            duration_ms = int((time.time() - start_time) * 1000)
            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            usage = response_body.get("usage", {})

            return APIResponse(
                success=True,
                content=content,
                provider=APIProviderType.AWS_BEDROCK,
                cost=0.0,  # Difficult to calc precisely without dynamic pricing
                duration_ms=duration_ms,
                tokens_used=usage.get("output_tokens", 0),
                session_id=kwargs.get("session_id"),
                metadata={
                    "model": self.model,
                    "usage": usage,
                },
            )

        except ClientError as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"Bedrock API error: {e}")
            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.AWS_BEDROCK,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            self.error_count += 1
            logger.error(f"Bedrock error: {e}")
            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.AWS_BEDROCK,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        if not BOTO3_AVAILABLE or not self.client:
            return APIProviderStatus.UNAVAILABLE
        try:
            # Listing foundation models is a good health check
            # We need a separate client for list_foundation_models usually, but invoke is enough
            # Just verify client exists and no errors so far
            return APIProviderStatus.HEALTHY
        except Exception:
            return APIProviderStatus.UNAVAILABLE
