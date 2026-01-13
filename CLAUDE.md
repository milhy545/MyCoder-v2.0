# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Note:** Also check `AGENTS.md` for latest project updates and shared context written by all AI agents (Claude, Jules/Gemini, Codex). When you make significant changes, document them in AGENTS.md's "Recent Changes" section.

## Project Overview

MyCoder v2.1.0 is a production-ready AI development assistant with a 5-tier API provider fallback system, Intel Q9550 thermal management, FEI-inspired architecture, and integrated speech recognition/dictation capabilities (repo: MyCoder-v2.0). This is a Poetry-managed Python project with comprehensive testing and Docker support.

## Core Architecture

### Multi-API Provider System
- **5-tier fallback**: Claude Anthropic API → Claude OAuth → Gemini → Ollama Local → Ollama Remote
- **Mercury Provider**: Alternative provider for fallback scenarios
- **Provider router**: `src/mycoder/api_providers.py` (1271 lines) handles intelligent provider selection
- **Thermal awareness**: Integrated Q9550 temperature monitoring affects provider selection

### Key Components
- **`src/mycoder/enhanced_mycoder_v2.py`** (897 lines): Main EnhancedMyCoderV2 class with multi-API integration
- **`src/mycoder/api_providers.py`** (1271 lines): All API provider implementations and routing logic
- **`src/mycoder/tool_registry.py`** (707 lines): FEI-inspired tool registry with execution contexts
- **`src/mycoder/adaptive_modes.py`** (671 lines): Thermal-aware operational mode management
- **`src/mycoder/config_manager.py`** (602 lines): Configuration management across providers
- **`src/speech_recognition/`**: Complete speech recognition and dictation system with Whisper/Gemini transcription

## Development Commands

### Project Setup
```bash
# Install dependencies (recommended)
poetry install

# Install with extras for HTTP features
poetry install --extras http

# Install with speech recognition support
poetry install --extras speech

# Without Poetry (fallback)
pip install -r requirements.txt
```

### CLI Commands (Poetry Scripts)
```bash
# Interactive MyCoder CLI
poetry run mycoder

# Run demo
poetry run mycoder-demo

# Launch dictation/speech recognition
poetry run dictation
```

### Testing Framework
```bash
# Unit tests (core functionality)
poetry run pytest tests/unit/ -v

# Integration tests (API interactions)
poetry run pytest tests/integration/ -v

# Functional tests (end-to-end workflows)
poetry run pytest tests/functional/ -v

# E2E tests (simulation-based end-to-end)
poetry run pytest tests/e2e/ -v

# Stress tests (system limits and Q9550 thermal)
python tests/stress/run_stress_tests.py --all
python tests/stress/run_stress_tests.py --quick     # Fast suites only
python tests/stress/run_stress_tests.py --suite thermal  # Requires Q9550

# Run tests by marker
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m thermal      # Requires Q9550 system
poetry run pytest -m network      # Requires network access
poetry run pytest -m auth         # Requires Claude CLI auth
```

### Code Quality
```bash
# Format code (Black + isort)
poetry run black . && poetry run isort .

# Linting
poetry run flake8 src/ tests/

# Type checking (strict mode enabled in pyproject.toml)
poetry run mypy src/
```

### Docker Development (Czech Makefile)
The project includes a comprehensive Czech-language Makefile with extensive Docker automation:

```bash
# Development with live reload
make dev              # Start development server with live reload
make dev-detached     # Start dev server in background
make dev-shell        # Open shell in development container
make dev-python       # Start Python shell in dev environment

# Production deployment
make prod             # Start production server
make prod-detached    # Start production in background

# Lightweight version (for limited resources: 2-4GB RAM, TinyLlama)
make light            # Ultra-lightweight version
make light-detached   # Lightweight in background

# Testing and debugging
make test             # Run tests in Docker
make test-integration # Run integration tests
make test-quick       # Quick smoke tests
make lint             # Run linting in Docker
make format           # Format code in Docker

# Container management
make logs             # View development logs
make logs-prod        # View production logs
make logs-light       # View lightweight logs
make status           # Show service status
make health           # Health check all services
make stop             # Stop all services
make restart          # Restart development server
make clean            # Clean Docker cache

# Build commands
make build-dev        # Rebuild development image
make build-prod       # Rebuild production image
make rebuild          # Rebuild all images

# Local Python development (without Docker)
make venv             # Create local venv and install dependencies via Poetry
make test-local       # Run tests locally
make lint-local       # Lint locally
make format-local     # Format locally
```

## Test Structure and Markers

### Test Categories
- **Unit tests** (`tests/unit/`): Core component functionality
- **Integration tests** (`tests/integration/`): Real API interactions
- **Functional tests** (`tests/functional/`): End-to-end workflows
- **E2E tests** (`tests/e2e/`): Simulation-based end-to-end scenarios
- **Stress tests** (`tests/stress/`): System limits and thermal management

### Test Markers (defined in pyproject.toml)
- `unit`: Unit tests
- `integration`: Integration tests
- `functional`: Functional tests
- `stress`: Stress tests
- `performance`: Performance tests
- `slow`: Slow running tests
- `network`: Tests requiring network access
- `thermal`: Tests requiring Q9550 thermal system
- `auth`: Tests requiring Claude CLI authentication

## Configuration Management

### Environment Variables
```bash
export ANTHROPIC_API_KEY="your_anthropic_key"
export GEMINI_API_KEY="your_gemini_key"
export MYCODER_DEBUG=1
export MYCODER_THERMAL_MAX_TEMP=75
export MYCODER_PREFERRED_PROVIDER=claude_oauth
```

### Configuration Files
- **`mycoder_config.json`**: Main configuration for all providers
- **`pyproject.toml`**: Project settings, dependencies, tool configurations (Black, isort, mypy, pytest)
- **`docker-compose*.yml`**: Three deployment modes (dev, prod, lightweight)
- **`dictation_config_local.json`**: Speech recognition configuration

## Thermal Management Integration

### Q9550 Specific Features
- **Temperature monitoring**: Real-time CPU temperature tracking
- **Automatic throttling**: Reduces AI workload when temperature exceeds 75°C
- **Emergency protection**: Hard shutdown at 85°C
- **PowerManagement integration**: Uses existing thermal scripts at `/home/milhy777/Develop/Production/PowerManagement/`

### Thermal Testing
```bash
# Full thermal stress testing (requires Q9550)
python tests/stress/run_stress_tests.py --suite thermal

# Skip thermal tests on non-Q9550 systems
poetry run pytest -m "not thermal"
```

## Speech Recognition Module

The `src/speech_recognition/` module provides comprehensive dictation and voice command capabilities:

### Components
- **`cli.py`**: Command-line interface for dictation (accessible via `poetry run dictation`)
- **`dictation_app.py`**: Main dictation application
- **`whisper_transcriber.py`**: OpenAI Whisper-based transcription
- **`gemini_transcriber.py`**: Google Gemini-based transcription
- **`audio_recorder.py`**: Audio capture and processing
- **`hotkey_manager.py`**: Keyboard shortcut management
- **`text_injector.py`**: Text insertion into applications
- **`overlay_button.py`**: UI overlay for dictation control
- **`setup_wizard.py`**: Initial configuration wizard

### Usage
```bash
# Launch dictation system
poetry run dictation

# Install with speech dependencies
poetry install --extras speech
```

## Package Structure

```
MyCoder-v2.0/
├── src/
│   ├── mycoder/                   # Core package
│   │   ├── enhanced_mycoder_v2.py     # Main class with 5-tier API system
│   │   ├── api_providers.py           # Provider implementations and router
│   │   ├── tool_registry.py           # FEI-inspired tool system
│   │   ├── adaptive_modes.py          # Thermal-aware modes
│   │   ├── config_manager.py          # Configuration management
│   │   └── cli.py                     # Main CLI interface
│   └── speech_recognition/        # Speech recognition and dictation module
│       ├── cli.py                 # Dictation CLI
│       ├── dictation_app.py       # Main dictation app
│       ├── whisper_transcriber.py # Whisper transcription
│       └── gemini_transcriber.py  # Gemini transcription
├── tests/
│   ├── unit/                      # Unit tests
│   ├── integration/               # API integration tests
│   ├── functional/                # End-to-end tests
│   ├── e2e/                       # Simulation-based E2E tests
│   ├── stress/                    # Stress and thermal tests
│   └── conftest.py                # Pytest configuration and fixtures
├── docs/                          # API documentation and guides
├── examples/                      # Usage examples and demos
└── Makefile                       # Development automation (Czech)
```

## Development Workflow

### Making Changes
1. **Run existing tests**: `poetry run pytest tests/unit/ -v`
2. **Code with style**: `poetry run black . && poetry run isort .`
3. **Type check**: `poetry run mypy src/`
4. **Add tests**: Follow existing test patterns in appropriate test category
5. **Verify coverage**: `poetry run pytest --cov=src --cov-report=html`

### Adding API Providers
1. **Implement provider**: Extend `BaseAPIProvider` class in `src/mycoder/api_providers.py`
2. **Update router**: Add provider to `APIProviderRouter` routing logic
3. **Add tests**: Create unit and integration tests
4. **Update config**: Add provider configuration schema

### Performance Benchmarks (Q9550 @ 2.83GHz)
- **Simple Query**: 0.5-2.0s (Claude OAuth, cached auth)
- **File Analysis**: 2.0-5.0s (Ollama Local inference)
- **Complex Task**: 5.0-15.0s (Claude Anthropic API)
- **Thermal Check**: <0.1s (Q9550 sensors, hardware direct)

## Tool Registry System

### Adding Tools
1. **Implement tool**: Create tool class extending base tool interface
2. **Register tool**: Add to tool registry in `src/mycoder/tool_registry.py`
3. **Set permissions**: Configure execution context and permissions
4. **Add tests**: Unit tests for tool functionality

### Tool Categories
- **File Operations**: Read, write, analyze files
- **MCP Integration**: Model Context Protocol tools
- **Thermal Monitoring**: Q9550 temperature tools
- **System Tools**: Performance and resource monitoring

## API Provider Priority Logic

The system intelligently selects providers based on:
1. **Thermal conditions**: Prefer local inference when CPU temp > 70°C
2. **Request complexity**: Route complex tasks to more capable providers
3. **Provider health**: Skip unhealthy providers in fallback chain
4. **Cost optimization**: Prefer free/cheaper options when appropriate
5. **Performance requirements**: Balance speed vs quality based on context

## Troubleshooting

### Common Issues
- **Thermal tests failing**: Ensure Q9550 system with PowerManagement scripts
- **Provider timeouts**: Check API keys and network connectivity
- **Memory errors**: Ensure 4GB+ RAM for full test suite
- **Docker build issues**: Use `make clean` then rebuild

### Debug Mode
```bash
# Enable debug logging
export MYCODER_DEBUG=1
poetry run python -m mycoder.enhanced_mycoder_v2

# Pytest with detailed output
poetry run pytest tests/unit/ -v -s --tb=long

# Docker debug shell
make dev-shell
```

This project emphasizes production reliability, thermal safety for Q9550 systems, and comprehensive testing across multiple AI providers.
