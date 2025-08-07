"""Claude CLI Authentication Module.

A production-ready Python module for Claude AI integration without API keys.
Uses Claude CLI authentication for seamless access to Claude Code capabilities.

Key Features:
- No API keys required (uses `claude auth login`)
- Triple fallback system (SDK → CLI → Error handling)
- Session persistence and management
- Production-ready error handling
- Memory optimized streaming
- Comprehensive testing coverage

Example:
    Basic usage:
    
    ```python
    from claude_cli_auth import ClaudeAuthManager
    from pathlib import Path
    
    claude = ClaudeAuthManager()
    response = await claude.query(
        "Explain this code",
        working_directory=Path(".")
    )
    print(response.content)
    ```

    With streaming:
    
    ```python
    async def on_stream(update):
        print(f"[{update.type}] {update.content}")
    
    response = await claude.query(
        "Create a Python function",
        stream_callback=on_stream
    )
    ```
"""

from .adaptive_modes import AdaptiveModeManager, OperationalMode
from .auth_manager import AuthManager
from .cli_interface import CLIInterface, CLIResponse
from .exceptions import (
    ClaudeAuthError,
    ClaudeAuthManagerError,
    ClaudeCLIError,
    ClaudeConfigError,
    ClaudeSessionError,
    ClaudeTimeoutError,
)
from .facade import ClaudeAuthManager
from .models import AuthConfig, ClaudeResponse, SessionInfo, StreamUpdate
from .mycoder import MyCoder

# Version info
__version__ = "1.1.0"
__author__ = "David Strejc"
__email__ = "strejc.david@gmail.com"
__license__ = "MIT"

# Public API
__all__ = [
    # Main interfaces
    "ClaudeAuthManager",
    "MyCoder",
    
    # Core components
    "AuthManager", 
    "CLIInterface",
    
    # Adaptive modes
    "AdaptiveModeManager",
    "OperationalMode",
    
    # Models
    "AuthConfig",
    "ClaudeResponse",
    "CLIResponse", 
    "SessionInfo",
    "StreamUpdate",
    
    # Exceptions
    "ClaudeAuthError",
    "ClaudeAuthManagerError", 
    "ClaudeCLIError",
    "ClaudeConfigError",
    "ClaudeSessionError",
    "ClaudeTimeoutError",
    
    # Metadata
    "__version__",
    "__author__", 
    "__email__",
    "__license__",
]

# Module-level configuration
import logging
import os

# Set up default logging if not configured
if not logging.getLogger(__name__).handlers:
    logging.basicConfig(
        level=logging.INFO if os.getenv("CLAUDE_DEBUG") else logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

# Disable debug logging for dependencies by default
for logger_name in ["httpx", "asyncio", "urllib3"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)