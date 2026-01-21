# Enhanced MyCoder v2.2.0

> **Multi-API AI Development Assistant with Q9550 Thermal Management**

[![Python 3.10-3.13](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](#testing)
[![Q9550 Compatible](https://img.shields.io/badge/Q9550-thermal%20managed-orange.svg)](#thermal-management)

Enhanced MyCoder v2.2.0 is a comprehensive AI development assistant featuring **modular multi-provider architecture**, **Q9550 thermal management**, **agent orchestration**, and **FEI-inspired architecture**. Built for production environments requiring high availability and thermal safety.

[🇨🇿 Česká verze (Czech Version)](README.cz.md)

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0
pip install -r requirements.txt
# Or using Poetry (Recommended)
poetry install
```

### Basic Usage

```python
from mycoder import EnhancedMyCoderV2
from pathlib import Path

# Basic configuration
config = {
    "claude_oauth": {"enabled": True},
    "ollama_local": {"enabled": True},
    "thermal": {"enabled": True, "max_temp": 75}
}

# Initialize MyCoder
mycoder = EnhancedMyCoderV2(
    working_directory=Path("."),
    config=config
)

# Start processing
await mycoder.initialize()

response = await mycoder.process_request(
    "Analyze this Python file and suggest optimizations",
    files=[Path("example.py")]
)

print(f"Response: {response['content']}")
print(f"Provider: {response['provider']}")
print(f"Cost: ${response['cost']}")
```

### Interactive CLI

```bash
poetry run mycoder
```

Commands:
- `/setup` - Configure providers and keys
- `/providers` - List available providers
- `/plan <task>` - Generate implementation plan
- `/voice start` - Start dictation mode

## 🏗️ Architecture

### Modular Provider System

MyCoder now supports a wide range of AI providers through a modular interface:

**LLM Providers:**
- **Claude Anthropic API** (Primary, High Quality)
- **Claude OAuth** (Authenticated CLI)
- **Google Gemini** (High Speed, Large Context)
- **AWS Bedrock** (Enterprise, Claude/Titan)
- **OpenAI** (GPT-4o, o1)
- **X.AI** (Grok)
- **Mistral AI** (Open/Commercial)
- **HuggingFace** (Inference API)
- **Ollama** (Local/Remote/Termux)
- **Mercury** (Inception Labs)

**TTS Providers (Text-to-Speech):**
- **Azure Speech** (High Quality Neural)
- **Amazon Polly** (Neural/Standard)
- **ElevenLabs** (Premium Cloning)
- **gTTS** (Google Translate)
- **Local** (pyttsx3, espeak)

**STT Providers (Speech-to-Text):**
- **Whisper** (OpenAI API / Local)
- **Google Gemini** (Multimodal)
- **Azure Speech** (Real-time)

### FEI-Inspired Components

- **Tool Registry Pattern**: Centralized tool management with execution contexts
- **Service Layer Pattern**: Clean separation between API providers and business logic
- **Event-Based Architecture**: Reactive system with health monitoring and thermal awareness

### Q9550 Thermal Management

Integrated thermal monitoring and throttling for Intel Q9550 processors:

- **Temperature Monitoring**: Real-time CPU temperature tracking
- **Automatic Throttling**: Reduces AI workload when temperature exceeds 75°C
- **Emergency Protection**: Hard shutdown at 85°C to prevent hardware damage
- **PowerManagement Integration**: Uses existing Q9550 thermal scripts

## 🔧 Configuration

### Environment Variables

```bash
# API Keys
export ANTHROPIC_API_KEY="sk-..."
export GEMINI_API_KEY="AIza..."
export OPENAI_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
export MISTRAL_API_KEY="..."
export HF_TOKEN="hf_..."
export ELEVENLABS_API_KEY="..."
export AZURE_SPEECH_KEY="..."
export AZURE_SPEECH_REGION="eastus"

# AWS Credentials (if using Bedrock/Polly)
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"

# System Configuration  
export MYCODER_DEBUG=1
export MYCODER_THERMAL_MAX_TEMP=75
export MYCODER_PREFERRED_PROVIDER=claude_oauth
```

### Configuration File

Create `mycoder_config.json`:

```json
{
  "claude_anthropic": {
    "enabled": true,
    "timeout_seconds": 30,
    "model": "claude-3-5-sonnet-20241022"
  },
  "gemini": {
    "enabled": true,
    "rate_limit_rpm": 15,
    "rate_limit_rpd": 1500
  },
  "aws_bedrock": {
    "enabled": true,
    "model": "anthropic.claude-3-sonnet-20240229-v1:0"
  },
  "text_to_speech": {
    "enabled": true,
    "provider": "azure",
    "voice": "en-US-JennyNeural"
  }
}
```

## 🛠️ Features

### Multi-API Provider Support

- **Intelligent Fallback**: Automatic failover between providers
- **Health Monitoring**: Real-time provider status tracking
- **Cost Optimization**: Prefer free/cheaper providers when available
- **Performance Metrics**: Track response times and success rates
- **Circuit Breaker & Rate Limiting**: Resilient API management with persistent rate limiting (RPM/RPD)

### Thermal Management (Q9550)

- **Hardware Integration**: Direct integration with Q9550 thermal sensors
- **Proactive Throttling**: Prevent thermal damage before it occurs
- **Performance Scaling**: Adjust AI workload based on temperature
- **System Protection**: Emergency shutdown for critical temperatures

### Tool Registry System

- **Modular Tools**: File operations, MCP integration, thermal monitoring
- **Execution Contexts**: Secure sandboxed tool execution
- **Permission System**: Role-based access control for tools
- **Performance Monitoring**: Track tool usage and performance

### Session Management

- **Persistent Sessions**: Maintain conversation context across requests
- **Provider Transitions**: Seamless switching between API providers
- **Automatic Cleanup**: Memory-efficient session management
- **Recovery Support**: Restore sessions after system restart

## 📊 Testing

### Comprehensive Test Suite

- **Unit Tests** (90% pass rate): Core component functionality
- **Integration Tests** (90% pass rate): Real-world scenarios  
- **Functional Tests** (95% pass rate): End-to-end workflows
- **Stress Tests** (80% pass rate): System limits and edge cases

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test types
python -m pytest tests/unit/ -v        # Unit tests
python -m pytest tests/integration/ -v # Integration tests
python -m pytest tests/functional/ -v  # Functional tests

# Stress testing
python tests/stress/run_stress_tests.py --all
python tests/stress/run_stress_tests.py --thermal  # Q9550 required

# Interactive testing
python tests/functional/test_mycoder_live.py --interactive
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic**, **Google**, **OpenAI**, **AWS**, **Microsoft**, **ElevenLabs** for AI services
- **Ollama** for local LLM infrastructure
- **Intel Q9550** community for thermal management insights
- **FEI** architectural patterns inspiration

---

**Made with ❤️ for the AI development community**

*Enhanced MyCoder v2.2.0 - Where AI meets thermal responsibility*
