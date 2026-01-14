from mycoder.api_providers import APIProviderConfig, APIProviderRouter, APIProviderType


def test_7tier_fallback_chain_order():
    configs = [
        APIProviderConfig(provider_type=APIProviderType.CLAUDE_ANTHROPIC, config={}),
        APIProviderConfig(provider_type=APIProviderType.CLAUDE_OAUTH, config={}),
        APIProviderConfig(provider_type=APIProviderType.GEMINI, config={}),
        APIProviderConfig(provider_type=APIProviderType.MERCURY, config={}),
        APIProviderConfig(
            provider_type=APIProviderType.OLLAMA_LOCAL,
            config={"base_url": "http://localhost:11434"},
        ),
        APIProviderConfig(
            provider_type=APIProviderType.TERMUX_OLLAMA,
            config={"base_url": "http://192.168.1.10:11434"},
        ),
        APIProviderConfig(
            provider_type=APIProviderType.OLLAMA_REMOTE,
            config={"base_url": "http://remote:11434"},
        ),
    ]

    router = APIProviderRouter(configs)
    assert router.fallback_chain == [
        APIProviderType.CLAUDE_ANTHROPIC,
        APIProviderType.CLAUDE_OAUTH,
        APIProviderType.GEMINI,
        APIProviderType.MERCURY,
        APIProviderType.OLLAMA_LOCAL,
        APIProviderType.TERMUX_OLLAMA,
        APIProviderType.OLLAMA_REMOTE,
    ]
