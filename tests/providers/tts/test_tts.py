"""
Tests for TTS Providers.
"""

import unittest
from mycoder.tts_engine import TTSEngine
from mycoder.providers.tts import BaseTTSProvider

class TestTTS(unittest.TestCase):

    def test_tts_engine_init(self):
        # pyttsx3 should be available or handled gracefully
        engine = TTSEngine(provider="pyttsx3")
        self.assertIsInstance(engine.provider, BaseTTSProvider)

    def test_tts_engine_fallback(self):
        # Invalid provider should fallback
        engine = TTSEngine(provider="invalid_provider")
        self.assertIsNotNone(engine.provider)
        self.assertIn(engine.provider_name, ["pyttsx3", "espeak", "gtts"])

if __name__ == "__main__":
    unittest.main()
