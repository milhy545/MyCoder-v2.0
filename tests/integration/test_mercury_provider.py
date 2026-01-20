import pytest

from mycoder.api_providers import APIProviderConfig, APIProviderType, MercuryProvider


@pytest.mark.asyncio
async def test_mercury_requires_api_key(monkeypatch):
    monkeypatch.delenv("INCEPTION_API_KEY", raising=False)
    config = APIProviderConfig(provider_type=APIProviderType.MERCURY, config={})
    provider = MercuryProvider(config)
    response = await provider.query("hello")
    assert response.success is False
    assert "INCEPTION_API_KEY" in (response.error or "")
