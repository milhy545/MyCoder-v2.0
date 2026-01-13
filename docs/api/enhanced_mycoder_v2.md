# Enhanced MyCoder v2.1.0 API Reference

## EnhancedMyCoderV2 Class

The main interface for Enhanced MyCoder v2.1.0 functionality.

### Constructor

```python
EnhancedMyCoderV2(
    working_directory: Path,
    config: dict = None,
    preferred_provider: str = None
)
```

**Parameters:**
- `working_directory` (Path): Directory for file operations and tool execution
- `config` (dict, optional): Configuration dictionary. If None, uses default configuration
- `preferred_provider` (str, optional): Preferred API provider name

**Example:**
```python
from mycoder import EnhancedMyCoderV2
from pathlib import Path

mycoder = EnhancedMyCoderV2(
    working_directory=Path("."),
    config={
        "claude_oauth": {"enabled": True},
        "thermal": {"enabled": True, "max_temp": 75}
    },
    preferred_provider="claude_oauth"
)
```

### Methods

#### `async initialize() -> None`

Initialize the MyCoder system, including API providers, tool registry, and thermal monitoring.

**Raises:**
- `RuntimeError`: If initialization fails
- `ConfigError`: If configuration is invalid

**Example:**
```python
await mycoder.initialize()
```

#### `async shutdown() -> None`

Cleanly shutdown the MyCoder system, closing connections and cleaning up resources.

**Example:**
```python
await mycoder.shutdown()
```

#### `async process_request(prompt: str, files: List[Path] = None, session_id: str = None, continue_session: bool = False, use_tools: bool = True) -> dict`

Process an AI request with optional file context and tool usage.

**Parameters:**
- `prompt` (str): The user's request/question
- `files` (List[Path], optional): List of files to include in context
- `session_id` (str, optional): Session identifier for conversation persistence
- `continue_session` (bool): Whether to continue existing session
- `use_tools` (bool): Whether to enable tool usage

**Returns:**
- `dict`: Response dictionary containing:
  - `success` (bool): Whether the request succeeded
  - `content` (str): The AI response content
  - `provider` (str): Which API provider was used
  - `cost` (float): Estimated cost in USD
  - `duration_ms` (int): Response time in milliseconds
  - `session_id` (str): Session identifier
  - `error` (str, optional): Error message if failed
  - `recovery_suggestions` (List[str], optional): Suggested recovery actions

**Example:**
```python
response = await mycoder.process_request(
    "Analyze this Python file for potential optimizations",
    files=[Path("example.py")],
    session_id="analysis_session",
    use_tools=True
)

print(f"Response: {response['content']}")
print(f"Provider: {response['provider']}")
print(f"Cost: ${response['cost']}")
```

#### `async get_system_status() -> dict`

Get comprehensive system status information.

**Returns:**
- `dict`: Status dictionary containing:
  - `status` (str): Overall system status
  - `working_directory` (str): Current working directory
  - `active_sessions` (int): Number of active sessions
  - `providers` (dict): Status of each API provider
  - `thermal` (dict): Thermal monitoring status
  - `tools` (dict): Tool registry statistics
  - `mode` (str): Current operational mode

**Example:**
```python
status = await mycoder.get_system_status()
print(f"Status: {status['status']}")
print(f"Active sessions: {status['active_sessions']}")
print(f"Thermal safe: {status['thermal']['safe_operation']}")
```

### Properties

#### `initialized: bool`

Whether the system has been initialized.

#### `working_directory: Path`

Current working directory for file operations.

#### `config: dict`

Current system configuration.

#### `session_store: dict`

Dictionary of active sessions.

## Configuration

### Configuration Structure

```python
{
    "claude_anthropic": {
        "enabled": bool,
        "timeout_seconds": int,
        "model": str,
        "api_key": str  # Optional, uses environment variable
    },
    "claude_oauth": {
        "enabled": bool,
        "timeout_seconds": int
    },
    "gemini": {
        "enabled": bool,
        "timeout_seconds": int,
        "model": str,
        "api_key": str  # Optional, uses environment variable
    },
    "ollama_local": {
        "enabled": bool,
        "base_url": str,
        "model": str,
        "timeout_seconds": int
    },
    "ollama_remote_urls": List[str],
    "thermal": {
        "enabled": bool,
        "max_temp": float,
        "critical_temp": float,
        "check_interval": int,
        "performance_script": str
    },
    "system": {
        "log_level": str,
        "enable_tool_registry": bool,
        "enable_mcp_integration": bool,
        "session_timeout_hours": int,
        "max_concurrent_requests": int
    },
    "debug_mode": bool,
    "preferred_provider": str,
    "fallback_enabled": bool
}
```

### Default Values

```python
DEFAULT_CONFIG = {
    "claude_anthropic": {
        "enabled": True,
        "timeout_seconds": 30,
        "model": "claude-3-5-sonnet-20241022"
    },
    "claude_oauth": {
        "enabled": True,
        "timeout_seconds": 45
    },
    "gemini": {
        "enabled": True,
        "timeout_seconds": 30,
        "model": "gemini-1.5-pro"
    },
    "ollama_local": {
        "enabled": True,
        "base_url": "http://localhost:11434",
        "model": "tinyllama",
        "timeout_seconds": 60
    },
    "thermal": {
        "enabled": True,
        "max_temp": 75.0,
        "critical_temp": 85.0,
        "check_interval": 30
    },
    "system": {
        "log_level": "INFO",
        "enable_tool_registry": True,
        "enable_mcp_integration": True
    },
    "debug_mode": False
}
```

## API Providers

### Provider Types

- **`CLAUDE_ANTHROPIC`**: Anthropic's Claude API (requires API key)
- **`CLAUDE_OAUTH`**: Claude via OAuth (free tier)
- **`GEMINI`**: Google's Gemini API (requires API key)
- **`OLLAMA_LOCAL`**: Local Ollama instance
- **`OLLAMA_REMOTE`**: Remote Ollama instances

### Provider Status

- **`HEALTHY`**: Provider is operational
- **`DEGRADED`**: Provider has issues but may work
- **`UNAVAILABLE`**: Provider is not accessible
- **`ERROR`**: Provider encountered an error

### Fallback Chain

Providers are tried in order of priority:
1. Preferred provider (if specified)
2. Claude Anthropic API (if API key available)
3. Claude OAuth (if authenticated)
4. Gemini API (if API key available)
5. Ollama Local (if running)
6. Ollama Remote instances (if configured)

## Tool Registry

### Available Tools

- **File Operations**: Read, write, list, exists operations
- **MCP Integration**: Model Context Protocol tools
- **Thermal Monitoring**: Q9550 temperature checking
- **System Tools**: Status reporting, health checks

### Tool Execution Modes

- **`FULL`**: All tools available
- **`DEGRADED`**: Limited tool set
- **`AUTONOMOUS`**: Local tools only
- **`RECOVERY`**: Emergency tools only

## Thermal Management

### Temperature Thresholds

- **Normal**: < 75°C (default max_temp)
- **High**: 75-85°C (throttling begins)
- **Critical**: > 85°C (emergency shutdown)

### Thermal Actions

1. **Normal Operation**: Full performance
2. **Throttling**: Reduced AI workload, longer timeouts
3. **Emergency Shutdown**: System protection mode

### Q9550 Integration

Requires PowerManagement scripts:
- `performance_manager.sh`: Temperature monitoring
- Hardware sensor access via `lm-sensors`
- Real-time thermal status reporting

## Error Handling

### Exception Types

- **`ConfigError`**: Configuration validation errors
- **`ProviderError`**: API provider errors
- **`ThermalError`**: Thermal management errors
- **`ToolError`**: Tool execution errors

### Recovery Suggestions

The system provides automatic recovery suggestions:
- Alternative providers to try
- Configuration fixes
- System health checks
- Thermal management actions

## Session Management

### Session Structure

```python
{
    "session_id": str,
    "created_at": float,
    "updated_at": float,
    "total_interactions": int,
    "last_context": dict,
    "last_response": dict,
    "mode": str,
    "thermal_status": dict
}
```

### Session Persistence

- Sessions are stored in memory
- Automatic cleanup after 24 hours (configurable)
- Maximum 100 sessions (configurable)
- Session data survives provider switches

## Performance Metrics

### Response Time Targets

- Simple queries: < 2 seconds
- File analysis: < 5 seconds
- Complex tasks: < 15 seconds
- System status: < 0.5 seconds

### Resource Usage

- Memory: ~200MB baseline, ~500MB under load
- CPU: Variable based on thermal limits
- Network: Minimal for local providers
- Storage: ~50MB installation

## Best Practices

### Configuration

```python
# Production configuration
config = {
    "claude_oauth": {"enabled": True, "timeout_seconds": 45},
    "ollama_local": {"enabled": True, "model": "llama2:7b"},
    "thermal": {"enabled": True, "max_temp": 75},
    "system": {"log_level": "WARNING"}
}
```

### Error Handling

```python
try:
    response = await mycoder.process_request(prompt)
    if not response["success"]:
        print(f"Request failed: {response['error']}")
        for suggestion in response.get("recovery_suggestions", []):
            print(f"Try: {suggestion}")
except Exception as e:
    print(f"System error: {e}")
```

### Resource Management

```python
# Always initialize and shutdown properly
mycoder = EnhancedMyCoderV2(working_directory=Path("."))
try:
    await mycoder.initialize()
    # ... use mycoder
finally:
    await mycoder.shutdown()
```

### Session Management

```python
# Use sessions for conversations
session_id = "my_conversation"
response1 = await mycoder.process_request(
    "Start a discussion about Python optimization",
    session_id=session_id
)

response2 = await mycoder.process_request(
    "Continue with specific examples",
    session_id=session_id,
    continue_session=True
)
```