"""
Tests for STT Providers.
"""

import unittest

from mycoder.providers.stt import WhisperProviderType, WhisperSTTProvider


class TestSTT(unittest.TestCase):

    def test_whisper_config(self):
        config = {"provider_type": "api", "api_key": "sk-test"}
        provider = WhisperSTTProvider(config)
        self.assertEqual(provider.provider_type, WhisperProviderType.API)

    def test_whisper_local_config(self):
        config = {"provider_type": "local", "local_model": "tiny"}
        provider = WhisperSTTProvider(config)
        self.assertEqual(provider.provider_type, WhisperProviderType.LOCAL)
        self.assertEqual(provider.local_model_name, "tiny")


if __name__ == "__main__":
    unittest.main()
