"""MyCoder v2.0 - Advanced AI Development Assistant.

An advanced AI-powered development assistant with adaptive modes and MCP integration.
Built on top of claude-cli-auth for seamless Claude AI access without API keys.

Key Features:
- Adaptive operational modes (FULL, DEGRADED, AUTONOMOUS, RECOVERY)
- MCP orchestrator integration with intelligent tool routing
- Enhanced AI capabilities with memory persistence
- Network detection and automatic fallback handling
- Production-ready error recovery

Example:
    Basic usage:
    
    ```python
    from claude_cli_auth import MyCoder
    from pathlib import Path
    
    mycoder = MyCoder()
    response = await mycoder.process_request(
        "Create a Python function that processes files",
        files=[Path("example.py")]
    )
    print(response["content"])
    ```

    With adaptive modes:
    
    ```python
    from claude_cli_auth import AdaptiveModeManager, OperationalMode
    
    manager = AdaptiveModeManager()
    await manager.set_mode(OperationalMode.FULL)
    current_mode = manager.get_current_mode()
    ```
"""

# Import core authentication from external package
from claude_cli_auth import (
    AuthManager,
    CLIInterface,
    CLIResponse,
    ClaudeAuthManager,
    ClaudeAuthError,
    ClaudeAuthManagerError,
    ClaudeCLIError,
    ClaudeConfigError,
    ClaudeSessionError,
    ClaudeTimeoutError,
    AuthConfig,
    ClaudeResponse,
    SessionInfo,
    StreamUpdate,
)

# Import MyCoder-specific components locally  
from .adaptive_modes import AdaptiveModeManager, OperationalMode
from .enhanced_mycoder import EnhancedMyCoder
from .mcp_connector import MCPConnector, MCPToolRouter
from .mycoder import MyCoder

# Version info
__version__ = "2.0.0"
__author__ = "David Strejc"
__email__ = "strejc.david@gmail.com"
__license__ = "MIT"

# Public API
__all__ = [
    # MyCoder interfaces
    "MyCoder",
    "EnhancedMyCoder",
    
    # Adaptive modes
    "AdaptiveModeManager",
    "OperationalMode",
    
    # MCP Integration
    "MCPConnector",
    "MCPToolRouter",
    
    # Core components (re-exported from claude-cli-auth)
    "ClaudeAuthManager",
    "AuthManager", 
    "CLIInterface",
    
    # Models (re-exported from claude-cli-auth)
    "AuthConfig",
    "ClaudeResponse",
    "CLIResponse", 
    "SessionInfo",
    "StreamUpdate",
    
    # Exceptions (re-exported from claude-cli-auth)
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