"""Enhanced MyCoder v2.0 - Multi-API AI Development Assistant.

A comprehensive AI-powered development assistant with multi-provider fallback,
Q9550 thermal management, and FEI-inspired architecture.

Key Features:
- 5-tier API provider fallback (Claude Anthropic, Claude OAuth, Gemini, Ollama Local, Ollama Remote)
- Q9550 thermal management integration
- FEI-inspired architecture with tool registry
- Comprehensive testing framework
- Configuration management with multiple sources
- Session persistence and recovery

Example:
    Basic usage:
    
    ```python
    from enhanced_mycoder_v2 import EnhancedMyCoderV2
    from pathlib import Path
    
    config = {
        "claude_oauth": {"enabled": True},
        "ollama_local": {"enabled": True},
        "thermal": {"enabled": True, "max_temp": 75}
    }
    
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config
    )
    
    await mycoder.initialize()
    
    response = await mycoder.process_request(
        "Analyze this code and suggest improvements",
        files=[Path("example.py")]
    )
    
    print(response["content"])
    ```

    With advanced configuration:
    
    ```python
    from config_manager import ConfigManager
    from api_providers import APIProviderRouter
    
    # Load configuration from file
    config_manager = ConfigManager("mycoder_config.json")
    config = config_manager.load_config()
    
    # Create with advanced settings
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config.dict(),
        preferred_provider="claude_oauth"
    )
    ```
"""

# Core components
from .enhanced_mycoder_v2 import EnhancedMyCoderV2
from .api_providers import (
    APIProviderRouter,
    APIProviderType,
    APIProviderConfig,
    APIResponse,
    APIProviderStatus,
    ClaudeAnthropicProvider,
    ClaudeOAuthProvider,
    GeminiProvider,
    OllamaProvider,
)
from .config_manager import (
    ConfigManager,
    MyCoderConfig,
    APIProviderSettings,
    ThermalSettings,
    SystemSettings,
    load_config,
    get_config_manager,
)
from .tool_registry import (
    get_tool_registry,
    ToolRegistry,
    ToolExecutionContext,
    ToolResult,
    ToolExecutionMode,
)

# Version info
__version__ = "2.0.0"
__author__ = "David Strejc"
__email__ = "strejc.david@gmail.com"
__license__ = "MIT"

# Public API
__all__ = [
    # Core interface
    "EnhancedMyCoderV2",
    
    # API Providers
    "APIProviderRouter",
    "APIProviderType",
    "APIProviderConfig", 
    "APIResponse",
    "APIProviderStatus",
    "ClaudeAnthropicProvider",
    "ClaudeOAuthProvider",
    "GeminiProvider",
    "OllamaProvider",
    
    # Configuration Management
    "ConfigManager",
    "MyCoderConfig",
    "APIProviderSettings",
    "ThermalSettings", 
    "SystemSettings",
    "load_config",
    "get_config_manager",
    
    # Tool Registry
    "get_tool_registry",
    "ToolRegistry",
    "ToolExecutionContext",
    "ToolResult",
    "ToolExecutionMode",
    
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
        level=logging.INFO if os.getenv("MYCODER_DEBUG") else logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

# Disable debug logging for dependencies by default
for logger_name in ["httpx", "aiohttp", "asyncio", "urllib3"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)