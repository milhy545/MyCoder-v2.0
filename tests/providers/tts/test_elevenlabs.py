"""
Tests for ElevenLabs TTS Provider.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from mycoder.providers.tts.elevenlabs import ElevenLabsProvider


class TestElevenLabsProvider(unittest.TestCase):
    def setUp(self):
        self.config = {"api_key": "test_key", "voice_id": "test_voice"}
        self.provider = ElevenLabsProvider(self.config)

    def test_init(self):
        self.assertEqual(self.provider.api_key, "test_key")
        self.assertEqual(self.provider.voice_id, "test_voice")
        self.assertIsNone(self.provider._voices_cache)

    @patch("urllib.request.urlopen")
    def test_get_available_voices_success(self, mock_urlopen):
        # Mock response data
        mock_response_data = {
            "voices": [
                {"name": "Rachel", "voice_id": "voice1"},
                {"name": "Josh", "voice_id": "voice2"},
            ]
        }

        # Configure mock
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Call method
        voices = self.provider.get_available_voices()

        # Verify results
        self.assertEqual(len(voices), 2)
        self.assertEqual(voices[0], "Rachel (voice1)")
        self.assertEqual(voices[1], "Josh (voice2)")

        # Verify caching (should be set)
        self.assertEqual(self.provider._voices_cache, voices)

        # Verify API call args
        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        request = args[0]
        self.assertEqual(request.full_url, "https://api.elevenlabs.io/v1/voices")
        self.assertEqual(request.headers["Xi-api-key"], "test_key")

    @patch("urllib.request.urlopen")
    def test_get_available_voices_caching(self, mock_urlopen):
        # Pre-fill cache
        self.provider._voices_cache = ["Cached Voice (id)"]

        # Call method
        voices = self.provider.get_available_voices()

        # Verify result is from cache
        self.assertEqual(voices, ["Cached Voice (id)"])

        # Verify NO API call was made
        mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_get_available_voices_api_error(self, mock_urlopen):
        # Mock error response (e.g., 401)
        mock_response = MagicMock()
        mock_response.status = 401
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        voices = self.provider.get_available_voices()

        self.assertEqual(voices, [])
        self.assertIsNone(self.provider._voices_cache)

    @patch("urllib.request.urlopen")
    def test_get_available_voices_exception(self, mock_urlopen):
        # Mock exception
        mock_urlopen.side_effect = Exception("Network error")

        voices = self.provider.get_available_voices()

        self.assertEqual(voices, [])
        self.assertIsNone(self.provider._voices_cache)

    def test_get_available_voices_no_api_key(self):
        provider = ElevenLabsProvider({}) # No key
        voices = provider.get_available_voices()
        self.assertEqual(voices, [])


if __name__ == "__main__":
    unittest.main()
