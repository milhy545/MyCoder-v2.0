# User Guide

Comprehensive user guide for Enhanced MyCoder v2.1.0.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Configuration](#configuration)
4. [Provider Management](#provider-management)
5. [Session Management](#session-management)
6. [Thermal Management](#thermal-management)
7. [Tool Registry](#tool-registry)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### First Steps

```python
from mycoder import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def main():
    # Basic configuration
    config = {
        "claude_oauth": {"enabled": True},
        "thermal": {"enabled": True}
    }
    
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config
    )
    
    await mycoder.initialize()
    
    response = await mycoder.process_request(
        "Help me understand this codebase structure"
    )
    
    print(response['content'])
    await mycoder.shutdown()

asyncio.run(main())
```

## Core Concepts

### 5-Tier API Provider System

Enhanced MyCoder v2.1.0 uses a sophisticated fallback system:

1. **Claude Anthropic API** (Premium)
   - Highest quality responses
   - Paid service with API key
   - Best for critical tasks

2. **Claude OAuth** (Authenticated)
   - High quality responses
   - Free with authentication
   - Recommended for daily use

3. **Gemini API** (Alternative)
   - Google's AI service
   - Different strengths and perspective
   - Good fallback option

4. **Ollama Local** (Private)
   - Runs on your machine
   - Complete privacy
   - Good for sensitive data

5. **Ollama Remote** (Distributed)
   - Remote Ollama instances
   - Load distribution
   - Backup when local fails

### Automatic Fallback

```python
# MyCoder automatically tries providers in order:
# 1. Your preferred provider
# 2. Next available healthy provider
# 3. Continue until request succeeds or all fail

response = await mycoder.process_request("Analyze this code")
# Might use claude_oauth, but fall back to ollama_local if needed
```

## Configuration

### Configuration Sources (Priority Order)

1. **Direct Configuration** (Highest priority)
2. **Environment Variables**
3. **Configuration Files**
4. **Default Values** (Lowest priority)

### Environment Variables

```bash
# API Keys
export ANTHROPIC_API_KEY="your_key"
export GEMINI_API_KEY="your_key"

# System Settings
export MYCODER_DEBUG=1                    # Enable debug logging
export MYCODER_PREFERRED_PROVIDER=claude_oauth
export MYCODER_THERMAL_ENABLED=true
export MYCODER_THERMAL_MAX_TEMP=75

# Provider Settings
export MYCODER_OLLAMA_LOCAL_URL=http://localhost:11434
export MYCODER_OLLAMA_REMOTE_URLS=http://server1:11434,http://server2:11434
```

### Configuration File

Create `mycoder_config.json`:

```json
{
  "providers": {
    "claude_anthropic": {
      "enabled": true,
      "timeout_seconds": 30,
      "model": "claude-3-5-sonnet-20241022",
      "max_tokens": 4096
    },
    "claude_oauth": {
      "enabled": true,
      "timeout_seconds": 45
    },
    "gemini": {
      "enabled": true,
      "timeout_seconds": 30,
      "model": "gemini-1.5-pro",
      "max_tokens": 4096
    },
    "ollama_local": {
      "enabled": true,
      "base_url": "http://localhost:11434",
      "model": "tinyllama",
      "timeout_seconds": 60
    },
    "ollama_remote": {
      "enabled": true,
      "urls": [
        "http://server1:11434",
        "http://server2:11434"
      ],
      "model": "tinyllama",
      "timeout_seconds": 90
    }
  },
  "thermal": {
    "enabled": true,
    "max_temp": 75.0,
    "critical_temp": 85.0,
    "check_interval": 30,
    "throttle_threshold": 0.8,
    "performance_script": "/path/to/performance_manager.sh"
  },
  "system": {
    "log_level": "INFO",
    "enable_tool_registry": true,
    "enable_mcp_integration": true,
    "max_concurrent_requests": 5,
    "default_timeout": 60
  },
  "session_management": {
    "max_sessions": 100,
    "session_timeout_hours": 24,
    "auto_cleanup": true,
    "persistence_enabled": true
  }
}
```

### Runtime Configuration

```python
from mycoder.config_manager import ConfigManager

# Load configuration
config_manager = ConfigManager("mycoder_config.json")
config = config_manager.load_config()

# Modify configuration
config_manager.update_provider_config("ollama_local", {
    "model": "llama2:13b",
    "timeout_seconds": 120
})

# Save changes
config_manager.save_config()
```

## Provider Management

### Provider Status

```python
# Check provider health
status = await mycoder.get_system_status()
print("Provider Status:")
for provider, info in status['providers'].items():
    print(f"- {provider}: {info['status']} ({info.get('response_time', 'N/A')}ms)")
```

### Provider Selection

```python
# Explicit provider selection
response = await mycoder.process_request(
    "Analyze this code",
    preferred_provider="claude_anthropic"
)

# Provider-specific requests
response = await mycoder.process_request(
    "Private analysis - keep local",
    preferred_provider="ollama_local",
    allow_fallback=False  # Don't fall back to remote providers
)
```

### Provider Configuration

```python
# Enable/disable providers at runtime
await mycoder.update_provider_status("gemini", enabled=False)

# Update provider settings
await mycoder.update_provider_config("ollama_local", {
    "model": "codellama:13b",
    "timeout_seconds": 180
})
```

## Session Management

### Creating Sessions

```python
# Automatic session creation
response = await mycoder.process_request(
    "Start new coding session",
    session_id="my_project_session"
)

# Session continues automatically
response2 = await mycoder.process_request(
    "Continue with the previous context",
    session_id="my_project_session",
    continue_session=True
)
```

### Session Persistence

```python
# List all sessions
sessions = await mycoder.list_sessions()
for session in sessions:
    print(f"Session: {session['id']} ({session['message_count']} messages)")

# Get session details
session_info = await mycoder.get_session_info("my_project_session")
print(f"Created: {session_info['created_at']}")
print(f"Last used: {session_info['last_used']}")
print(f"Total cost: ${session_info['total_cost']:.4f}")

# Clean up old sessions
cleaned = await mycoder.cleanup_sessions(max_age_hours=48)
print(f"Cleaned up {cleaned} old sessions")
```

### Session Recovery

```python
# Sessions persist across MyCoder restarts
mycoder = EnhancedMyCoderV2(...)
await mycoder.initialize()

# Previous sessions are automatically available
response = await mycoder.process_request(
    "What were we discussing?",
    session_id="my_project_session",
    continue_session=True
)
```

## Thermal Management

### Q9550 Integration

Enhanced MyCoder v2.1.0 includes special support for Intel Q9550 processors:

```python
# Enable thermal management
config = {
    "thermal": {
        "enabled": True,
        "max_temp": 75.0,        # Start throttling at 75°C
        "critical_temp": 85.0,   # Emergency shutdown at 85°C
        "check_interval": 30,    # Check every 30 seconds
        "performance_script": "/home/user/performance_manager.sh"
    }
}
```

### Thermal Monitoring

```python
# Check current thermal status
status = await mycoder.get_system_status()
thermal = status.get('thermal', {})

print(f"Current Temperature: {thermal.get('current_temp')}°C")
print(f"Safe Operation: {thermal.get('safe_operation')}")
print(f"Throttling Active: {thermal.get('throttling_active')}")

# Thermal history
history = await mycoder.get_thermal_history()
print(f"Max temp in last hour: {history['max_temp_1h']}°C")
print(f"Throttling events: {history['throttle_events']}")
```

### Thermal Behavior

- **Normal Operation** (< 75°C): Full AI processing capacity
- **Throttling** (75-85°C): Reduced request frequency and complexity
- **Emergency Mode** (> 85°C): Pause AI processing, emergency cooling
- **Recovery** (< 70°C): Gradually resume normal operation

## Tool Registry

### Available Tools

```python
# List available tools
tools = await mycoder.get_available_tools()
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")
```

### File Operations

```python
# Read file
response = await mycoder.process_request(
    "Read and analyze the content of config.py",
    files=[Path("config.py")]
)

# Write file
response = await mycoder.process_request(
    "Create a new Python script that implements a simple calculator",
    output_file=Path("calculator.py")
)

# Edit file
response = await mycoder.process_request(
    "Add error handling to this function",
    files=[Path("utils.py")],
    edit_mode=True
)
```

### System Tools

```python
# Execute commands (sandboxed)
response = await mycoder.process_request(
    "Check the current git status and suggest next steps"
)

# Environment analysis
response = await mycoder.process_request(
    "Analyze the current development environment and suggest improvements"
)
```

## Best Practices

### Configuration Best Practices

1. **Use Environment Variables** for sensitive data:
   ```bash
   export ANTHROPIC_API_KEY="your_key"
   # Don't put API keys in config files
   ```

2. **Layer Configuration** appropriately:
   ```python
   # Base configuration in file
   # Override with environment
   # Fine-tune with runtime settings
   ```

3. **Enable Thermal Management** on supported hardware:
   ```python
   config["thermal"]["enabled"] = True
   ```

### Request Best Practices

1. **Use Sessions** for related requests:
   ```python
   session_id = "project_analysis"
   # All related requests use same session_id
   ```

2. **Specify Files** when relevant:
   ```python
   response = await mycoder.process_request(
       "Optimize this function",
       files=[Path("slow_function.py")]
   )
   ```

3. **Handle Errors Gracefully**:
   ```python
   if not response['success']:
       print(f"Request failed: {response['error']}")
       # Handle failure appropriately
   ```

### Performance Best Practices

1. **Choose Appropriate Providers**:
   - Use `claude_oauth` for general development
   - Use `ollama_local` for private/sensitive code
   - Use `claude_anthropic` for critical/complex tasks

2. **Manage Sessions**:
   ```python
   # Clean up old sessions regularly
   await mycoder.cleanup_sessions(max_age_hours=24)
   ```

3. **Monitor System Health**:
   ```python
   # Regular health checks
   status = await mycoder.get_system_status()
   if status['status'] != 'healthy':
       # Take appropriate action
   ```

### Security Best Practices

1. **API Key Management**:
   ```bash
   # Use environment variables
   export ANTHROPIC_API_KEY="your_key"
   
   # Set proper permissions
   chmod 600 ~/.bashrc
   ```

2. **File Access**:
   ```python
   # MyCoder operates within working_directory
   # Don't process untrusted files
   ```

3. **Network Security**:
   ```python
   # Configure Ollama remote URLs securely
   # Use VPN or secure networks
   ```

## Troubleshooting

### Common Issues

#### 1. Provider Authentication Errors

```python
# Check API keys
import os
print("ANTHROPIC_API_KEY:", "✓" if os.getenv('ANTHROPIC_API_KEY') else "✗")
print("GEMINI_API_KEY:", "✓" if os.getenv('GEMINI_API_KEY') else "✗")

# Test Claude OAuth
# Run: claude auth whoami
```

#### 2. Connection Issues

```python
# Check provider connectivity
status = await mycoder.get_system_status()
for provider, info in status['providers'].items():
    if info['status'] != 'healthy':
        print(f"{provider}: {info['status']} - {info.get('error', 'Unknown error')}")
```

#### 3. Thermal Issues

```bash
# Check if sensors are working
sensors

# Install missing thermal tools
sudo apt-get install lm-sensors
sudo sensors-detect
```

#### 4. Ollama Issues

```bash
# Check Ollama status
ollama list
curl http://localhost:11434/api/version

# Start Ollama if needed
ollama serve
```

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export MYCODER_DEBUG=1
```

#### Get System Information

```python
# Comprehensive system status
status = await mycoder.get_system_status()
print(json.dumps(status, indent=2))

# Provider-specific diagnostics
for provider in ['claude_oauth', 'ollama_local']:
    info = await mycoder.get_provider_info(provider)
    print(f"{provider}: {info}")
```

#### Test Individual Components

```python
# Test configuration loading
from mycoder.config_manager import ConfigManager
config_manager = ConfigManager("mycoder_config.json")
config = config_manager.load_config()
print("Configuration loaded successfully")

# Test thermal monitoring
from thermal_manager import ThermalManager
thermal = ThermalManager()
temp = await thermal.get_current_temperature()
print(f"Current temperature: {temp}°C")
```

### Performance Issues

#### High CPU Usage

1. Check thermal throttling:
   ```python
   status = await mycoder.get_system_status()
   if status['thermal']['throttling_active']:
       print("System is thermal throttling")
   ```

2. Reduce concurrent requests:
   ```python
   config['system']['max_concurrent_requests'] = 2
   ```

#### Slow Response Times

1. Check provider status:
   ```python
   status = await mycoder.get_system_status()
   for provider, info in status['providers'].items():
       print(f"{provider}: {info.get('avg_response_time', 'N/A')}ms")
   ```

2. Use faster providers:
   ```python
   # Prefer local providers for speed
   config['preferred_provider'] = 'ollama_local'
   ```

#### Memory Issues

1. Clean up sessions:
   ```python
   await mycoder.cleanup_sessions(max_age_hours=1)
   ```

2. Reduce session retention:
   ```python
   config['session_management']['max_sessions'] = 50
   ```

### Getting Help

- **Documentation**: [Full API Documentation](../api/)
- **Examples**: [Code Examples](../examples/)
- **Issues**: [GitHub Issues](https://github.com/milhy545/MyCoder-v2.0/issues)
- **Discussions**: [GitHub Discussions](https://github.com/milhy545/MyCoder-v2.0/discussions)

### Advanced Topics

For advanced usage including:
- Custom provider development
- MCP integration
- Docker deployment
- CI/CD integration

See the [Advanced Guide](advanced_guide.md) and [API Documentation](../api/).