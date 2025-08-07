# 🤖 MyCoder v2.0 - Advanced AI Development Assistant

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-brightgreen.svg)](https://github.com/milhy545/MyCoder-v2.0)

**MyCoder v2.0** is an advanced AI-powered development assistant that intelligently adapts to your environment, network conditions, and available resources. It provides seamless Claude AI integration without API keys and includes comprehensive MCP (Model Context Protocol) orchestration.

## 🌟 Key Features

### 🎯 **Adaptive Intelligence**
- **4 Operational Modes**: FULL, DEGRADED, AUTONOMOUS, RECOVERY
- **Automatic Mode Switching**: Based on network conditions and resource availability
- **Intelligent Fallbacks**: Local operations when cloud services unavailable
- **Health Monitoring**: Continuous system health assessment and adaptation

### 🔗 **MCP Integration**
- **27 MCP Tools**: File operations, Git, Terminal, Database, Memory, Research
- **Orchestrator Connection**: Seamless integration with MCP orchestrator (192.168.0.58:8020)
- **Smart Tool Routing**: Mode-aware tool availability and fallback strategies
- **Memory Persistence**: Advanced context and session management

### 🔐 **Claude Authentication**
- **No API Keys Required**: Uses Claude CLI authentication (`claude auth login`)
- **Subscription Compatible**: Works with Claude subscription instead of API access
- **Triple Fallback System**: SDK → CLI → Local operations
- **Session Management**: Persistent conversations across mode transitions
- **Modular Design**: Built on the separate [claude-cli-authentication](https://github.com/milhy545/claude-cli-authentication) module

## 🚀 Quick Start

### Installation

**Automatic Installation (Recommended):**
```bash
curl -sSL https://raw.githubusercontent.com/milhy545/MyCoder-v2.0/main/install_mycoder.sh | bash
```

**Manual Installation:**
```bash
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0
poetry install
poetry shell
```

**Installation Paths:**
- Main project: `~/MyCoder-v2.0/`
- Source code: `~/MyCoder-v2.0/src/mycoder/`
- Virtual environment: `~/MyCoder-v2.0/.venv/`
- Configuration: `~/.mycoder_aliases`
- Total size: ~80-150 MB

### Basic Usage

```python
from mycoder import EnhancedMyCoder
from pathlib import Path

# Initialize MyCoder with automatic mode detection
mycoder = EnhancedMyCoder(working_directory=Path("."))
await mycoder.initialize()

# AI-powered code review with memory persistence
result = await mycoder.process_request(
    "Review this code and suggest improvements",
    files=["app.py", "models.py"],
    use_mcp_memory=True,
    research_context=True
)

print(result['content'])
print(f"Mode used: {result['mode']}")
print(f"MCP tools: {result['mcp_tools_used']}")
```

### Demo Script

```bash
# Run interactive demo
mycoder-demo
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 Your Application                │
├─────────────────────────────────────────────────┤
│              EnhancedMyCoder                    │
│          (Adaptive AI Assistant)                │
├─────────────────────────────────────────────────┤
│  AdaptiveModeManager    │    MCPConnector       │
│  • Health Monitoring   │    • 27 Tools         │ 
│  • Auto Mode Switch    │    • Smart Routing    │
│  • 4 Modes Support     │    • Local Fallbacks  │
├─────────────────────────────────────────────────┤
│  Claude CLI Auth        │    MCP Orchestrator   │
│  • Session Management  │    • File Operations   │
│  • No API Keys         │    • Git Integration   │
│  • Subscription Mode   │    • Memory Service    │
└─────────────────────────────────────────────────┘
```

## 🎮 Operational Modes

### 🟢 **FULL Mode** (Optimal Environment)
- **Requirements**: Stable internet, MCP orchestrator available, Claude authenticated
- **Capabilities**: All 27 MCP tools, full AI features, research capabilities
- **Use Case**: Home/office development with full connectivity

### 🟡 **DEGRADED Mode** (Limited Connectivity)
- **Requirements**: Claude authenticated, limited network
- **Capabilities**: Essential tools (11 selected), basic AI features
- **Use Case**: Unstable network, traveling, limited bandwidth

### 🟠 **AUTONOMOUS Mode** (Offline AI)
- **Requirements**: Local resources only
- **Capabilities**: Local LLM (Ollama), basic file operations (5 tools)
- **Use Case**: No internet, offline development, privacy-focused

### 🔴 **RECOVERY Mode** (Emergency)
- **Requirements**: Minimal system access
- **Capabilities**: File operations only, emergency procedures
- **Use Case**: System issues, debugging, emergency access

## 📚 Documentation

- **[Adaptive Modes Guide](MYCODER_ADAPTIVE_MODES_DESIGN.md)** - Detailed mode documentation
- **[Czech Documentation](docs/cs/README.md)** - Česká dokumentace
- **[English Documentation](docs/en/README.md)** - Complete English guide

## 🧪 Testing

```bash
# Test adaptive modes
python test_adaptive_modes.py

# Test MCP integration  
python test_enhanced_mycoder.py

# Interactive demo
python demo_mycoder.py
```

## 📦 Components

MyCoder v2.0 includes these major components:

- **`EnhancedMyCoder`**: Main AI assistant interface
- **`AdaptiveModeManager`**: Intelligent mode switching
- **`MCPConnector`**: MCP orchestrator integration  
- **`MCPToolRouter`**: Smart tool routing with fallbacks
- **`ClaudeAuthManager`**: Claude authentication without API keys

## 🎯 Use Cases

- **Solo Development**: AI pair programming with context awareness
- **Team Projects**: Shared memory and consistent code review
- **Remote Work**: Adaptive performance based on network conditions
- **Offline Development**: Autonomous mode for privacy/security
- **CI/CD Integration**: Automated code review and testing
- **Learning**: Interactive coding tutor with persistent memory

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**MyCoder v2.0** - Where adaptive intelligence meets development excellence! 🚀