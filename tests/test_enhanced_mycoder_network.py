import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import asyncio

# Ensure the root directory is in sys.path
sys.path.append(os.getcwd())

from src.enhanced_mycoder_v2 import EnhancedMyCoderV2

class TestEnhancedMyCoderNetwork(unittest.TestCase):
    def setUp(self):
        # We need to mock get_tool_registry to avoid issues during init
        self.patcher = patch('src.enhanced_mycoder_v2.get_tool_registry')
        self.mock_registry = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_get_network_target_default(self):
        mycoder = EnhancedMyCoderV2(config={
            "ollama_local_enabled": True,
            "ollama_local_url": "http://localhost:11434"
        })
        host, port = mycoder._get_network_target()
        self.assertEqual(host, "localhost")
        self.assertEqual(port, 11434)

    def test_get_network_target_remote(self):
        mycoder = EnhancedMyCoderV2(config={
            "ollama_local_enabled": False,
            "ollama_remote_urls": ["http://remote-server:8080"]
        })
        host, port = mycoder._get_network_target()
        self.assertEqual(host, "remote-server")
        self.assertEqual(port, 8080)

    def test_get_network_target_fallback(self):
        mycoder = EnhancedMyCoderV2(config={
            "ollama_local_enabled": False,
            "ollama_remote_urls": []
        })
        host, port = mycoder._get_network_target()
        self.assertEqual(host, "1.1.1.1")
        self.assertEqual(port, 53)

    @patch('socket.create_connection')
    def test_check_network_status_excellent(self, mock_create):
        mycoder = EnhancedMyCoderV2()

        # Simulate fast connection
        mock_create.return_value.close.return_value = None

        # We need to mock time.time to control latency measurement
        with patch('time.time', side_effect=[100.0, 100.010, 100.010]): # 10ms diff
            status = mycoder._check_network_status("localhost", 11434)

        self.assertTrue(status["connected"])
        self.assertEqual(status["quality"], "excellent")
        self.assertEqual(status["latency_ms"], 10.0)

    @patch('socket.create_connection')
    def test_check_network_status_offline(self, mock_create):
        mycoder = EnhancedMyCoderV2()

        # Simulate connection failure
        mock_create.side_effect = OSError("Unreachable")

        status = mycoder._check_network_status("localhost", 11434)

        self.assertFalse(status["connected"])
        self.assertEqual(status["quality"], "offline")
        self.assertIn("Unreachable", status.get("error", ""))

if __name__ == '__main__':
    unittest.main()
