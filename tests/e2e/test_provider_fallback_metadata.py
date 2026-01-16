"""Fallback metadata tests for API provider router."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from mycoder.api_providers import (
    APIProviderConfig,
    APIProviderRouter,
    APIProviderStatus,
    APIProviderType,
    APIResponse,
    BaseAPIProvider,
)


class DummyProvider(BaseAPIProvider):
    """Deterministic provider for fallback testing."""

    def __init__(
        self,
        config: APIProviderConfig,
        responses: List[bool],
        error_message: str = "boom",
    ) -> None:
        super().__init__(config)
        self._responses = responses
        self._error_message = error_message
        self._index = 0

    async def query(
        self, prompt: str, context: Dict[str, Any] = None, **kwargs
    ) -> APIResponse:
        self.total_requests += 1
        success = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        if success:
            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY
            return APIResponse(
                success=True,
                content=f"ok:{self.config.provider_type.value}",
                provider=self.config.provider_type,
                metadata={},
            )

        self.error_count += 1
        self.status = APIProviderStatus.UNAVAILABLE
        return APIResponse(
            success=False,
            content="",
            provider=self.config.provider_type,
            error=self._error_message,
        )

    async def health_check(self) -> APIProviderStatus:
        return APIProviderStatus.HEALTHY


def _load_fixture() -> Dict[str, Any]:
    fixture_path = Path(__file__).parent / "fixtures" / "fallback_metadata.json"
    return json.loads(fixture_path.read_text())


def _build_router(providers: List[DummyProvider]) -> APIProviderRouter:
    router = APIProviderRouter([])
    router.providers = providers
    router.fallback_chain = [provider.config.provider_type for provider in providers]
    return router


def _expected_case(name: str) -> Dict[str, Any]:
    fixture = _load_fixture()
    for case in fixture["cases"]:
        if case["name"] == name:
            return case["expected"]
    raise AssertionError(f"Missing fixture case: {name}")


def test_fallback_metadata_on_success_after_failure() -> None:
    expected = _expected_case("fallback_success")

    provider_1 = DummyProvider(
        APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH, max_retries=1),
        responses=[False],
    )
    provider_2 = DummyProvider(
        APIProviderConfig(provider_type=APIProviderType.GEMINI, max_retries=1),
        responses=[True],
    )

    router = _build_router([provider_1, provider_2])
    response = _run_query(router)

    assert response.success is True
    metadata = response.metadata or {}
    assert metadata.get("fallback_used") == expected["fallback_used"]
    assert metadata.get("attempted_providers") == expected["attempted_providers"]
    assert metadata.get("attempted_errors") == expected["attempted_errors"]


def test_fallback_metadata_on_retry_success() -> None:
    expected = _expected_case("retry_success")

    provider_1 = DummyProvider(
        APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH, max_retries=2),
        responses=[False, True],
    )

    router = _build_router([provider_1])
    response = _run_query(router)

    assert response.success is True
    metadata = response.metadata or {}
    assert metadata.get("fallback_used") == expected["fallback_used"]
    assert metadata.get("attempted_providers") == expected["attempted_providers"]
    assert metadata.get("attempted_errors") == expected["attempted_errors"]


def test_fallback_disabled_failure_metadata() -> None:
    expected = _expected_case("fallback_disabled_failure")

    provider_1 = DummyProvider(
        APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH, max_retries=1),
        responses=[False],
    )
    provider_2 = DummyProvider(
        APIProviderConfig(provider_type=APIProviderType.GEMINI, max_retries=1),
        responses=[True],
    )

    router = _build_router([provider_1, provider_2])
    response = _run_query(router, fallback_enabled=False)

    assert response.success is False
    metadata = response.metadata or {}
    assert metadata.get("fallback_used") == expected["fallback_used"]
    assert metadata.get("attempted_providers") == expected["attempted_providers"]
    assert metadata.get("attempted_errors") == expected["attempted_errors"]


def _run_query(router: APIProviderRouter, fallback_enabled: bool = True) -> APIResponse:
    return _run_query_sync(router, fallback_enabled)


def _run_query_sync(router: APIProviderRouter, fallback_enabled: bool) -> APIResponse:
    import asyncio

    async def _inner() -> APIResponse:
        return await router.query(
            prompt="Hello",
            context={},
            preferred_provider=APIProviderType.CLAUDE_OAUTH,
            fallback_enabled=fallback_enabled,
        )

    return asyncio.run(_inner())
