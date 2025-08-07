# Claude CLI Authentication Module

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A robust, production-ready Python module for Claude AI integration without API keys. Uses Claude CLI authentication for seamless access to Claude Code capabilities.

## 🎯 Key Features

- **No API Keys Required**: Uses Claude CLI authentication (`claude auth login`)
- **Triple Fallback System**: SDK → CLI → Error handling
- **Session Persistence**: Intelligent session management and recovery
- **Production Ready**: Comprehensive error handling and logging
- **Easy Integration**: Simple unified interface for any Python project
- **Memory Optimized**: Efficient streaming and bounded buffers

## 🚀 Quick Start

### Installation

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Authenticate with Claude
claude auth login

# Install this module
pip install claude-cli-auth
```

### Basic Usage

```python
from claude_cli_auth import ClaudeAuthManager
from pathlib import Path

# Initialize
claude = ClaudeAuthManager()

# Simple query
response = await claude.query(
    "Explain this code briefly",
    working_directory=Path(".")
)

print(response.content)
print(f"Cost: ${response.cost:.4f}")
```

## 📚 Documentation

- [English Documentation](docs/en/README.md)
- [Česká dokumentace](docs/cs/README.md)
- [API Reference](docs/api.md)
- [Integration Examples](examples/)

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│           Your Application          │
├─────────────────────────────────────┤
│        ClaudeAuthManager            │
│         (Unified Interface)         │
├─────────────────────────────────────┤
│  Primary: Python SDK + CLI Auth    │
│  Fallback: Direct CLI Subprocess   │
│  Emergency: Error Recovery         │
├─────────────────────────────────────┤
│        Claude CLI (~/.claude/)     │
└─────────────────────────────────────┘
```

## 🔧 Core Components

- **`AuthManager`**: Session and credential management
- **`CLIInterface`**: Direct CLI subprocess wrapper
- **`SDKInterface`**: Python SDK with CLI authentication
- **`Facade`**: Unified API with intelligent fallbacks

## ⚡ Advanced Usage

```python
# Streaming with callbacks
async def on_stream(update):
    print(f"[{update.type}] {update.content}")

response = await claude.query(
    "Create a Python function to parse JSON",
    working_directory=Path("./src"),
    stream_callback=on_stream,
    session_id="my-session"
)

# Session management
session_info = await claude.get_session_info("my-session")
sessions = await claude.list_sessions()
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=claude_cli_auth

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
```

## 🎨 Examples

- [Basic Integration](examples/basic_usage.py)
- [Streaming Interface](examples/streaming.py)
- [Session Management](examples/sessions.py)
- [Error Handling](examples/error_handling.py)
- [MyCoder Integration](examples/mycoder_integration.py)

## 🚨 Error Handling

The module provides comprehensive error handling for all common scenarios:

- **Authentication Issues**: Automatic re-login prompts
- **Network Problems**: Intelligent retry with backoff
- **Session Expiration**: Automatic session recovery
- **Tool Validation**: Security-aware tool filtering
- **Memory Management**: Bounded buffers and cleanup

## 🔒 Security Features

- **Credential Protection**: Secure token storage in `~/.claude/`
- **Tool Validation**: Configurable allowed/blocked tools
- **Session Isolation**: User-specific session management
- **Rate Limiting**: Built-in request throttling
- **Audit Logging**: Comprehensive operation tracking

## 🤝 Integration

Originally developed for MyCoder project and extracted as reusable module. Compatible with:

- Telegram bots (tested in production)
- Web applications
- CLI tools
- Jupyter notebooks
- Docker containers

## 🐛 Troubleshooting

See [Troubleshooting Guide](docs/troubleshooting.md) for common issues and solutions.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Note**: This module requires Claude Code CLI to be installed and authenticated. It does not use or require Anthropic API keys.