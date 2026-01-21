"""
Tests for LLM Providers.
"""

import unittest
from mycoder.api_providers import (
    APIProviderType,
    APIProviderConfig,
    GeminiProvider,
    ClaudeAnthropicProvider,
    OllamaProvider,
    BedrockProvider,
    OpenAIProvider
)

class TestLLMProviders(unittest.TestCase):

    def test_gemini_config(self):
        config = APIProviderConfig(
            provider_type=APIProviderType.GEMINI,
            config={"api_key": "test_key", "rate_limit_rpm": 20}
        )
        provider = GeminiProvider(config)
        self.assertEqual(provider.rate_limiter.rpm, 20)
        self.assertEqual(provider.rate_limiter.rpd, 1500) # Default if not set

    def test_bedrock_config(self):
        config = APIProviderConfig(
            provider_type=APIProviderType.AWS_BEDROCK,
            config={"region": "us-west-2"}
        )
        provider = BedrockProvider(config)
        self.assertEqual(provider.region, "us-west-2")

    def test_openai_config(self):
        config = APIProviderConfig(
            provider_type=APIProviderType.OPENAI,
            config={"api_key": "sk-test", "base_url": "https://custom.openai.com"}
        )
        provider = OpenAIProvider(config)
        self.assertEqual(provider.base_url, "https://custom.openai.com")

if __name__ == "__main__":
    unittest.main()
