
import asyncio
import http.server
import json
import logging
import threading
import time
import pytest
import pytest_asyncio
import os
from pathlib import Path
from src.enhanced_mycoder_v2 import EnhancedMyCoderV2
from src.api_providers import APIProviderType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Server Configuration
MOCK_SERVER_PORT = 11435  # Use non-standard port to avoid conflict
MOCK_SERVER_HOST = "localhost"
BASE_CONFIG = {
    "ollama_local_enabled": True,
    "ollama_local_model": "tinyllama",
    "ollama_local_base_url": f"http://{MOCK_SERVER_HOST}:{MOCK_SERVER_PORT}",
    "network_check_host": MOCK_SERVER_HOST,
    "network_check_port": MOCK_SERVER_PORT,
    "claude_anthropic_enabled": False,
    "claude_oauth_enabled": False,
    "gemini_enabled": False,
}

class MockLLMHandler(http.server.BaseHTTPRequestHandler):
    """Mock handler for Ollama API"""

    response_content = "Default response"

    def do_POST(self):
        """Handle POST requests to generate endpoint"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        request_json = json.loads(post_data.decode('utf-8'))

        logger.info(f"Mock Server received POST: {request_json}")

        # Determine response based on prompt
        prompt = request_json.get("prompt", "").lower()
        response_text = self.__class__.response_content

        response_data = {
            "response": response_text,
            "eval_count": 10,
            "eval_duration": 1000000
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_GET(self):
        """Handle GET requests for version check"""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Mock Ollama Server v0.0.1")

    def log_message(self, format, *args):
        """Silence server logging"""
        pass

class MockServerThread(threading.Thread):
    """Thread wrapper for Mock Server"""

    def __init__(self):
        super().__init__()
        self.server = http.server.HTTPServer((MOCK_SERVER_HOST, MOCK_SERVER_PORT), MockLLMHandler)
        self.daemon = True

    def run(self):
        logger.info(f"Starting Mock Server on {MOCK_SERVER_HOST}:{MOCK_SERVER_PORT}")
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()

@pytest.fixture(scope="module")
def mock_server():
    """Pytest fixture to start/stop mock server"""
    # Check if port is in use and kill if necessary (simple approach)
    # in a real env we might pick a random port

    server_thread = MockServerThread()
    server_thread.start()

    # Wait for server to start
    time.sleep(1)

    yield server_thread

    # Teardown
    server_thread.shutdown()

@pytest_asyncio.fixture
async def initialized_coder(mock_server):
    config = dict(BASE_CONFIG)
    coder = EnhancedMyCoderV2(config=config)
    await coder.initialize()
    try:
        yield coder
    finally:
        await coder.shutdown()

@pytest.mark.asyncio
async def test_network_connectivity(initialized_coder):
    """Test 1: Verify network status check against mock server"""

    # Execute a simple request
    # The prompt doesn't matter much for this test, we care about the context/metadata
    MockLLMHandler.response_content = "I am connected."

    result = await initialized_coder.process_request("Check network status")

    # Verify processing success
    assert result["success"] is True
    assert result["provider"] == "ollama_local"

    # Verify network status in session/metadata (we need to access internal session store or debug logs)
    # Since process_request returns 'metadata' which comes from APIResponse, let's see if we exposed network status there.
    # Looking at code: context["network_status"] is passed to tool context.
    # It is NOT explicitly returned in APIResponse metadata unless we put it there.
    # However, 'EnhancedMyCoderV2.process_request' logs it or uses it.
    # To verify it, we can inspect 'coder.session_store' if session_id is used,
    # OR we can call the public/internal method _check_network_status directly.

    status = initialized_coder._check_network_status()
    logger.info(f"Network Status Verified: {status}")

    assert status["connected"] is True
    assert status["quality"] == "excellent" # Localhost should be < 20ms
    assert status["target"] == f"{MOCK_SERVER_HOST}:{MOCK_SERVER_PORT}"

@pytest.mark.asyncio
async def test_update_dependencies_simulation(initialized_coder):
    """Test 2: Verify routing logic for 'Update dependencies'"""

    # SIMULATION: LLM decides to run a command
    MockLLMHandler.response_content = "I will run command: poetry update to refresh dependencies."

    # Execute request
    result = await initialized_coder.process_request("Update dependencies")

    # Verify
    assert result["success"] is True

    # Check content for simulated execution log
    logger.info(f"Result Content: {result['content']}")
    assert "Command Execution:" in result["content"]
    assert "Would execute 'poetry update'" in result["content"]

    # Verify metadata
    assert "command_execution" in result["metadata"]["tools_used"]
