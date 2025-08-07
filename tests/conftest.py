"""Pytest configuration and fixtures for claude-cli-auth tests.

Provides common fixtures and configuration for all test modules.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest
from claude_cli_auth import AuthConfig, AuthManager, ClaudeAuthManager


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
def mock_claude_config_dir(temp_dir: Path) -> Path:
    """Create a mock Claude config directory with credentials."""
    config_dir = temp_dir / ".claude"
    config_dir.mkdir()
    
    # Create mock credentials file
    credentials_file = config_dir / ".credentials.json"
    credentials_file.write_text('{"access_token": "mock_token"}')
    
    return config_dir


@pytest.fixture
def test_config(mock_claude_config_dir: Path, temp_dir: Path) -> AuthConfig:
    """Create a test configuration."""
    return AuthConfig(
        claude_config_dir=mock_claude_config_dir,
        working_directory=temp_dir,
        timeout_seconds=30,
        max_turns=5,
        use_sdk=False,  # Disable SDK by default to avoid dependency issues
        allowed_tools=["Read", "Write", "Edit", "Bash"],
    )


@pytest.fixture
def mock_auth_manager(test_config: AuthConfig) -> Generator[AuthManager, None, None]:
    """Create a mock AuthManager for testing."""
    with patch('claude_cli_auth.auth_manager.AuthManager._run_claude_command') as mock_cmd:
        # Mock successful authentication
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test@example.com"
        mock_result.stderr = ""
        mock_cmd.return_value = mock_result
        
        # Mock finding Claude CLI
        with patch('claude_cli_auth.auth_manager.AuthManager._find_claude_cli') as mock_find:
            mock_find.return_value = "/usr/local/bin/claude"
            
            auth_manager = AuthManager(test_config)
            yield auth_manager


@pytest.fixture
def claude_manager(test_config: AuthConfig) -> Generator[ClaudeAuthManager, None, None]:
    """Create a ClaudeAuthManager for testing."""
    with patch('claude_cli_auth.auth_manager.AuthManager._run_claude_command') as mock_cmd:
        # Mock successful authentication
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test@example.com"
        mock_result.stderr = ""
        mock_cmd.return_value = mock_result
        
        # Mock finding Claude CLI
        with patch('claude_cli_auth.auth_manager.AuthManager._find_claude_cli') as mock_find:
            mock_find.return_value = "/usr/local/bin/claude"
            
            # Disable SDK to avoid import issues in tests
            manager = ClaudeAuthManager(
                config=test_config,
                prefer_sdk=False,
                enable_fallback=False,
            )
            yield manager


@pytest.fixture
async def claude_manager_async(claude_manager: ClaudeAuthManager) -> AsyncGenerator[ClaudeAuthManager, None]:
    """Async version of claude_manager fixture."""
    yield claude_manager
    await claude_manager.shutdown()


@pytest.fixture
def mock_claude_cli_success():
    """Mock successful Claude CLI execution."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"type": "result", "result": "Hello! This is a test response.", "session_id": "test-session", "cost_usd": 0.05, "duration_ms": 1000, "num_turns": 1}'
    mock_result.stderr = ""
    
    return mock_result


@pytest.fixture
def mock_claude_cli_failure():
    """Mock failed Claude CLI execution."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Authentication failed"
    
    return mock_result


@pytest.fixture
def mock_claude_process():
    """Mock Claude CLI subprocess for async testing."""
    class MockProcess:
        def __init__(self, returncode=0, stdout_data="", stderr_data=""):
            self.returncode = returncode
            self.stdout = MockStream(stdout_data)
            self.stderr = MockStream(stderr_data)
            self.pid = 12345
            
        async def wait(self):
            return self.returncode
            
        def kill(self):
            pass
    
    class MockStream:
        def __init__(self, data: str):
            self.data = data.encode()
            self.position = 0
            
        async def read(self, size=-1):
            if self.position >= len(self.data):
                return b""
            
            if size == -1:
                result = self.data[self.position:]
                self.position = len(self.data)
            else:
                result = self.data[self.position:self.position + size]
                self.position += len(result)
                
            return result
        
        async def readline(self):
            if self.position >= len(self.data):
                return b""
            
            # Find next newline
            newline_pos = self.data.find(b'\n', self.position)
            if newline_pos == -1:
                result = self.data[self.position:]
                self.position = len(self.data)
            else:
                result = self.data[self.position:newline_pos + 1]
                self.position = newline_pos + 1
                
            return result
    
    return MockProcess


@pytest.fixture
def sample_claude_responses():
    """Sample Claude CLI responses for testing."""
    return [
        '{"type": "system", "subtype": "init", "tools": ["Read", "Write"], "model": "claude-3-5-sonnet"}',
        '{"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello! I can help you with that."}]}}',
        '{"type": "tool_result", "tool_use_id": "123", "result": {"content": "File read successfully"}}',
        '{"type": "result", "result": "Task completed successfully", "session_id": "test-session-123", "cost_usd": 0.025, "duration_ms": 1500, "num_turns": 2}'
    ]


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "CLAUDE_DEBUG": "1",
        "CLAUDE_CLI_PATH": "/usr/local/bin/claude",
    }):
        yield


# Test markers for different types of tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring Claude CLI authentication"
    )


# Skip tests that require authentication if not available
def pytest_runtest_setup(item):
    """Setup function that runs before each test."""
    # Skip auth tests if Claude CLI is not authenticated
    if item.get_closest_marker("auth"):
        try:
            import subprocess
            result = subprocess.run(
                ["claude", "auth", "whoami"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                pytest.skip("Claude CLI not authenticated - run 'claude auth login'")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Claude CLI not available or not authenticated")
    
    # Skip network tests if requested
    if item.get_closest_marker("network") and item.config.getoption("--skip-network"):
        pytest.skip("Network tests skipped")


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
        help="Run tests that require Claude CLI authentication"
    )