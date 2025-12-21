# Claude CLI Authentication Module - English Documentation

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Robust, production-ready Python module for integrating with Claude AI **without API keys**. Uses Claude CLI authentication for seamless access to Claude Code functionality.

## 🎯 Key Features

- **No API Keys Required**: Uses Claude CLI authentication (`claude auth login`)
- **Triple Fallback System**: SDK → CLI → Graceful error handling
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

### With Streaming and Session Management

```python
# Streaming callback
async def on_stream(update):
    print(f"[{update.type}] {update.content}")

response = await claude.query(
    "Create a Python function",
    working_directory=Path("./src"),
    stream_callback=on_stream,
    session_id="my-project-session"
)

# Continue conversation
response2 = await claude.query(
    "Add error handling to that function",
    session_id="my-project-session",
    continue_session=True
)
```

## 📚 Complete Usage

### Session Management

```python
# List all sessions
sessions = claude.list_sessions()

# Get session details
session = claude.get_session("my-project-session")
if session:
    print(f"Total cost: ${session.total_cost:.4f}")
    print(f"Messages: {session.total_turns}")

# Clean up old sessions
cleaned = await claude.cleanup_sessions()
print(f"Cleaned {cleaned} expired sessions")
```

### Configuration

```python
from claude_cli_auth import AuthConfig

config = AuthConfig(
    timeout_seconds=60,           # Query timeout
    max_turns=10,                 # Max conversation turns
    session_timeout_hours=48,     # Session expiration
    allowed_tools=["Read", "Write", "Edit", "Bash"],
    use_sdk=True,                 # Prefer SDK over CLI
    enable_streaming=True,        # Enable streaming
)

claude = ClaudeAuthManager(config=config)
```

### Monitoring and Statistics

```python
# Health check
if claude.is_healthy():
    print("✅ System is healthy")

# Usage statistics
stats = claude.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Average duration: {stats['avg_duration_ms']:.0f}ms")

# Configuration details
config_info = claude.get_config()
print(f"SDK available: {config_info['sdk_available']}")
print(f"CLI interface: {'✅' if config_info['cli_interface_initialized'] else '❌'}")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│           Your Application          │
├─────────────────────────────────────┤
│        ClaudeAuthManager            │
│         (Main Interface)            │
├─────────────────────────────────────┤
│  Primary: Python SDK + CLI Auth    │
│  Fallback: Direct CLI Subprocess   │
│  Emergency: Error Recovery          │
├─────────────────────────────────────┤
│        Claude CLI (~/.claude/)     │
└─────────────────────────────────────┘
```

## 🔧 Core Components

- **`AuthManager`**: Session and credential management
- **`CLIInterface`**: Direct CLI subprocess wrapper
- **`SDKInterface`**: Python SDK with CLI authentication (optional)
- **`ClaudeAuthManager`**: Unified API with intelligent fallbacks

## 🔍 Error Handling

The module provides comprehensive error handling for all common scenarios:

### Error Types

```python
from claude_cli_auth import (
    ClaudeAuthError,           # Base authentication error
    ClaudeConfigError,         # Configuration issues
    ClaudeSessionError,        # Session problems
    ClaudeTimeoutError,        # Timeouts
    ClaudeCLIError,           # CLI execution errors
    ClaudeParsingError,       # Response parsing errors
)

try:
    response = await claude.query("Test query")
except ClaudeAuthError as e:
    print(f"Authentication problem: {e.message}")
    print(f"Suggestions: {'; '.join(e.suggestions)}")
except ClaudeTimeoutError as e:
    print(f"Timeout after {e.details['timeout']} seconds")
```

### Automatic Problem Resolution

- **Authentication issues**: Automatic re-login prompts
- **Network problems**: Intelligent retry with backoff
- **Session expiration**: Automatic session recovery
- **Tool validation**: Security-aware tool filtering
- **Memory management**: Bounded buffers and cleanup

## ⚙️ Advanced Features

### Adaptive Modes

The module automatically detects available methods and switches between them:

```python
# At home with full access
claude = ClaudeAuthManager(
    prefer_sdk=True,        # Prefer SDK
    enable_fallback=True    # Allow CLI fallback
)

# Limited environment (CLI only)
claude = ClaudeAuthManager(
    prefer_sdk=False,       # CLI only
    enable_fallback=False   # No fallback
)
```

### Batch Operations

```python
# Multiple queries in sequence
queries = [
    "Analyze this file",
    "Suggest improvements", 
    "Create tests"
]

session_id = "batch-session"
for i, query in enumerate(queries):
    response = await claude.query(
        query,
        session_id=session_id,
        continue_session=i > 0
    )
    print(f"Response {i+1}: {response.content[:100]}...")
```

## 🚨 Troubleshooting

### Common Issues

1. **"Claude CLI not authenticated"**
   ```bash
   claude auth login
   ```

2. **"Claude CLI not found"**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

3. **"Session expired"**
   ```python
   # Sessions expire after 24 hours (configurable)
   await claude.cleanup_sessions()
   ```

4. **"Usage limit reached"**
   - Wait for limit reset
   - Use smaller queries
   - Check usage with `claude.get_stats()`

### Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug for module
logging.getLogger("claude_cli_auth").setLevel(logging.DEBUG)
```

## 📖 Integration Examples

### With Flask/FastAPI

```python
from flask import Flask, request, jsonify
from claude_cli_auth import ClaudeAuthManager

app = Flask(__name__)
claude = ClaudeAuthManager()

@app.route('/ask', methods=['POST'])
async def ask_claude():
    try:
        data = request.json
        response = await claude.query(
            prompt=data['question'],
            working_directory=Path(data.get('project_dir', '.')),
            session_id=data.get('session_id')
        )
        
        return jsonify({
            'response': response.content,
            'session_id': response.session_id,
            'cost': response.cost
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### With Telegram Bot

```python
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

claude = ClaudeAuthManager()

async def handle_message(update: Update, context):
    try:
        user_id = update.effective_user.id
        response = await claude.query(
            prompt=update.message.text,
            user_id=user_id,
            session_id=f"telegram_{user_id}"
        )
        
        await update.message.reply_text(response.content)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Setup Telegram bot...
```

## 🔒 Security

- **Credential Protection**: Secure token storage in `~/.claude/`
- **Tool Validation**: Configurable allowed/blocked tools
- **Session Isolation**: User-specific session management
- **Rate Limiting**: Built-in request throttling
- **Audit Logging**: Comprehensive operation tracking

## 🤝 Contributing

This module was originally developed for the MyCoder project and extracted as a reusable module. Compatible with:

- Telegram bots (production tested)
- Web applications
- CLI tools
- Jupyter notebooks
- Docker containers

## 📄 License

MIT License - see [LICENSE](../../LICENSE) for details.

---

**Note**: This module requires installed and authenticated Claude Code CLI. It does not use or require Anthropic API keys.