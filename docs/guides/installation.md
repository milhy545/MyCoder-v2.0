# Installation Guide

Complete installation guide for Enhanced MyCoder v2.1.0.

## System Requirements

- **Python**: 3.10-3.13 (recommended: 3.11)
- **Operating System**: Linux, macOS, Windows
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space
- **Hardware**: Q9550 processor for thermal management (optional)

## Installation Methods

### MiniPC 32-bit (Intel Atom)

If you are on a 32-bit system, follow the optimized profile:

- Use `poetry install --extras http`
- Copy `mycoder_config_minipc_32bit.json` to `mycoder_config.json`
- See `docs/guides/minipc_32bit.md` for detailed guidance

### Method 1: Git Clone (Recommended)

```bash
# Clone the repository
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "from mycoder import EnhancedMyCoderV2; print('✅ Installation successful')"
```

### Method 2: Development Installation

```bash
# Clone with development dependencies
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify
python -m pytest tests/unit/ -v
```

### Method 3: Docker Installation

```bash
# Pull the image
docker pull milhy545/mycoder-v2.0:latest

# Or build locally
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0
docker build -t mycoder-v2.0 .

# Run container
docker run -it --name mycoder mycoder-v2.0
```

## Configuration Setup

### 1. Environment Variables

```bash
# API Keys (optional)
export ANTHROPIC_API_KEY="your_anthropic_key"
export GEMINI_API_KEY="your_gemini_key"

# System Configuration
export MYCODER_DEBUG=1
export MYCODER_THERMAL_MAX_TEMP=75
export MYCODER_PREFERRED_PROVIDER=claude_oauth
```

### 2. Configuration File

Create `mycoder_config.json`:

```json
{
  "claude_anthropic": {
    "enabled": true,
    "timeout_seconds": 30,
    "model": "claude-3-5-sonnet-20241022"
  },
  "claude_oauth": {
    "enabled": true,
    "timeout_seconds": 45
  },
  "gemini": {
    "enabled": true,
    "timeout_seconds": 30,
    "model": "gemini-1.5-pro"
  },
  "ollama_local": {
    "enabled": true,
    "base_url": "http://localhost:11434",
    "model": "tinyllama"
  },
  "thermal": {
    "enabled": true,
    "max_temp": 75,
    "critical_temp": 85
  }
}
```

### 3. Q9550 Thermal Management Setup

For Q9550 systems with thermal management:

```bash
# Install thermal monitoring tools
sudo apt-get install lm-sensors

# Configure sensors
sudo sensors-detect

# Test thermal readings
sensors
```

## Provider Setup

### Claude Anthropic API

1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your_key_here"
   ```

### Claude OAuth

1. Install Claude CLI:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
2. Authenticate:
   ```bash
   claude auth login
   ```

### Google Gemini

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your_key_here"
   ```

### Ollama Local

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull tinyllama

# Verify Ollama is running
ollama list
```

### Ollama Remote

Configure remote Ollama instances in `mycoder_config.json`:

```json
{
  "ollama_remote_urls": [
    "http://server1:11434",
    "http://server2:11434"
  ]
}
```

## Verification

### Basic Functionality Test

```python
from mycoder import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def test_installation():
    config = {
        "claude_oauth": {"enabled": True},
        "thermal": {"enabled": False}  # Disable for basic test
    }
    
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config
    )
    
    try:
        await mycoder.initialize()
        status = await mycoder.get_system_status()
        print(f"✅ System Status: {status['status']}")
        print(f"✅ Available Providers: {len(status['providers'])}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await mycoder.shutdown()

# Run test
if __name__ == "__main__":
    success = asyncio.run(test_installation())
    exit(0 if success else 1)
```

### Run Test Suite

```bash
# Quick test
python tests/functional/test_mycoder_live.py --quick

# Full test suite
python -m pytest tests/ -v --tb=short
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'mycoder'**
   ```bash
   pip install -r requirements.txt
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **API Provider Authentication Errors**
   ```bash
   # Check environment variables
   env | grep -E "(ANTHROPIC|GEMINI)_API_KEY"
   
   # Check Claude OAuth
   claude auth whoami
   ```

3. **Thermal Management Not Working**
   ```bash
   # Install sensors
   sudo apt-get install lm-sensors
   
   # Test sensors
   sensors
   
   # Disable thermal if not needed
   export MYCODER_THERMAL_ENABLED=false
   ```

4. **Ollama Connection Issues**
   ```bash
   # Check Ollama is running
   curl http://localhost:11434/api/version
   
   # Start Ollama if needed
   ollama serve
   ```

### Performance Optimization

1. **For Q9550 Systems**:
   ```bash
   # Enable thermal management
   export MYCODER_THERMAL_ENABLED=true
   export MYCODER_THERMAL_MAX_TEMP=75
   ```

2. **For Development**:
   ```bash
   # Enable debug logging
   export MYCODER_DEBUG=1
   
   # Use fast local providers
   export MYCODER_PREFERRED_PROVIDER=ollama_local
   ```

3. **For Production**:
   ```bash
   # Disable debug
   export MYCODER_DEBUG=0
   
   # Use reliable providers
   export MYCODER_PREFERRED_PROVIDER=claude_oauth
   ```

## Next Steps

1. **Read the User Guide**: [docs/guides/user_guide.md](user_guide.md)
2. **Explore Examples**: [examples/](../../examples/)
3. **Run Interactive Tests**: [tests/functional/test_mycoder_live.py](../../tests/functional/test_mycoder_live.py)
4. **Check API Documentation**: [docs/api/](../api/)

## Support

- **GitHub Issues**: [Report installation problems](https://github.com/milhy545/MyCoder-v2.0/issues)
- **Documentation**: [Full documentation](../README.md)
- **Community**: [GitHub Discussions](https://github.com/milhy545/MyCoder-v2.0/discussions)
