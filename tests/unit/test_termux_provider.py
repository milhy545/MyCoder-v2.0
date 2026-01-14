import pytest

from mycoder.api_providers import (
    APIProviderConfig,
    APIProviderStatus,
    APIProviderType,
    APIResponse,
    TermuxOllamaProvider,
    OllamaProvider,
)


class DummyResponse:
    def __init__(self, status=200):
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, url):
        return DummyResponse(status=200)


@pytest.mark.asyncio
async def test_termux_health_check(monkeypatch):
    monkeypatch.setattr("mycoder.api_providers.aiohttp.ClientSession", DummySession)
    config = APIProviderConfig(
        provider_type=APIProviderType.TERMUX_OLLAMA,
        config={"base_url": "http://192.168.1.10:11434"},
    )
    provider = TermuxOllamaProvider(config)
    status = await provider.health_check()
    assert status == APIProviderStatus.HEALTHY


@pytest.mark.asyncio
async def test_termux_query_sets_provider(monkeypatch):
    async def fake_query(self, prompt, context=None, **kwargs):
        return APIResponse(
            success=True,
            content="ok",
            provider=APIProviderType.OLLAMA_REMOTE,
            duration_ms=1,
        )

    monkeypatch.setattr(OllamaProvider, "query", fake_query)
    config = APIProviderConfig(
        provider_type=APIProviderType.TERMUX_OLLAMA,
        config={"base_url": "http://192.168.1.10:11434"},
    )
    provider = TermuxOllamaProvider(config)
    response = await provider.query("hi")
    assert response.provider == APIProviderType.TERMUX_OLLAMA
