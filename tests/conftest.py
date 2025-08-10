"""Pytest configuration and fixtures for Enhanced MyCoder v2.0 tests.

Provides common fixtures and configuration for all test modules.
"""

import asyncio
import os
import tempfile
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir: Path) -> dict:
    """Create a test configuration for MyCoder v2.0."""
    return {
        "claude_anthropic": {
            "enabled": False,  # Disable by default for tests
            "timeout_seconds": 30
        },
        "claude_oauth": {
            "enabled": True,
            "timeout_seconds": 45
        },
        "gemini": {
            "enabled": False,  # Disable by default for tests  
            "timeout_seconds": 30
        },
        "ollama_local": {
            "enabled": True,
            "base_url": "http://localhost:11434",
            "model": "tinyllama",
            "timeout_seconds": 60
        },
        "thermal": {
            "enabled": False,  # Disable by default for tests
            "max_temp": 75
        },
        "system": {
            "log_level": "WARNING",  # Reduce noise in tests
            "enable_tool_registry": True
        },
        "debug_mode": False
    }


@pytest.fixture
def enhanced_mycoder(temp_dir: Path, test_config: dict):
    """Create an Enhanced MyCoder v2.0 instance for testing."""
    from enhanced_mycoder_v2 import EnhancedMyCoderV2
    
    return EnhancedMyCoderV2(
        working_directory=temp_dir,
        config=test_config
    )


@pytest.fixture
async def initialized_mycoder(enhanced_mycoder):
    """Create and initialize Enhanced MyCoder v2.0 instance."""
    await enhanced_mycoder.initialize()
    yield enhanced_mycoder
    await enhanced_mycoder.shutdown()


@pytest.fixture
def mock_api_response():
    """Mock successful API response."""
    from api_providers import APIResponse, APIProviderType
    
    return APIResponse(
        success=True,
        content="Mock API response for testing",
        provider=APIProviderType.OLLAMA_LOCAL,
        cost=0.0,
        duration_ms=500
    )


@pytest.fixture
def mock_failed_response():
    """Mock failed API response."""
    from api_providers import APIResponse, APIProviderType
    
    return APIResponse(
        success=False,
        content="",
        provider=APIProviderType.CLAUDE_OAUTH,
        error="Mock API failure for testing"
    )


@pytest.fixture
def sample_test_files(temp_dir: Path) -> list[Path]:
    """Create sample test files."""
    files = []
    
    # Python file
    py_file = temp_dir / "test_script.py"
    py_file.write_text('''def hello_world():
    """A simple test function."""
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
''')
    files.append(py_file)
    
    # Text file
    txt_file = temp_dir / "test_doc.txt"
    txt_file.write_text("This is a test document for MyCoder v2.0 testing.")
    files.append(txt_file)
    
    # JSON file
    json_file = temp_dir / "test_config.json"
    json_file.write_text('{"test": true, "version": "2.0", "items": [1, 2, 3]}')
    files.append(json_file)
    
    return files


@pytest.fixture
def mock_thermal_status():
    """Mock thermal status for Q9550 testing."""
    return {
        "cpu_temp": 70.0,
        "status": "normal",
        "safe_operation": True,
        "timestamp": "2024-01-15T10:30:00Z"
    }


@pytest.fixture  
def mock_tool_execution_context(temp_dir: Path):
    """Mock tool execution context."""
    from tool_registry import ToolExecutionContext
    
    return ToolExecutionContext(
        mode="FULL",
        working_directory=temp_dir,
        session_id="test_session"
    )


# Test markers for different types of tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test") 
    config.addinivalue_line("markers", "functional: mark test as a functional test")
    config.addinivalue_line("markers", "stress: mark test as a stress test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "network: mark test as requiring network access")
    config.addinivalue_line("markers", "thermal: mark test as requiring Q9550 thermal system")
    config.addinivalue_line("markers", "auth: mark test as requiring authentication")


def pytest_runtest_setup(item):
    """Setup function that runs before each test."""
    # Skip thermal tests if Q9550 system not available
    if item.get_closest_marker("thermal"):
        thermal_script = Path("/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh")
        if not thermal_script.exists():
            pytest.skip("Q9550 thermal system not available")
    
    # Skip network tests if requested
    if item.get_closest_marker("network") and item.config.getoption("--skip-network", default=False):
        pytest.skip("Network tests skipped")
    
    # Skip auth tests if not enabled
    if item.get_closest_marker("auth") and not item.config.getoption("--run-auth", default=False):
        pytest.skip("Authentication tests skipped (use --run-auth to enable)")


def pytest_addoption(parser):
    """Add command-line options for pytest."""
    parser.addoption(
        "--skip-network",
        action="store_true",
        default=False, 
        help="Skip tests that require network access"
    )
    parser.addoption(
        "--run-auth",
        action="store_true",
        default=False,
        help="Run tests that require authentication"
    )
    parser.addoption(
        "--skip-thermal",
        action="store_true",
        default=False,
        help="Skip Q9550 thermal management tests"
    )
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip slow running tests"
    )