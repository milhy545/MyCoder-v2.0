# Repository Guidelines

**Note:** This is a collaborative file maintained by all AI agents working on this project (Claude Code, Jules/Gemini, Codex). When you make significant changes to the project, document them in the Recent Changes section below.

## Recent Changes & Updates
*Agents: Add entries here when making significant changes*
- 2026-01-08: Claude Code - Expanded AGENTS.md to serve as comprehensive shared context for all AI agents
- 2026-01-08: Claude Code - Created CLAUDE.md with detailed Claude Code-specific workflows
- 2026-01-08: Claude Code - Updated GEMINI.md with reference to AGENTS.md
- 2026-01-13: Codex - Moved core modules into `src/mycoder`, updated imports/entrypoints/docs, added MiniPC 32-bit profile config+guide, and added public API unit test

## Project Overview

**Enhanced MyCoder v2.1.0** is a production-ready AI development assistant designed for high availability, performance, and thermal safety. Built with Python 3.10-3.13, managed via Poetry.

**Key Features:**
- **5-Tier API Provider Fallback:** Claude Anthropic API → Claude OAuth → Gemini → Ollama Local → Ollama Remote
- **Q9550 Thermal Management:** Real-time CPU temperature monitoring, automatic throttling, emergency protection
- **FEI-Inspired Architecture:** Tool Registry Pattern, Service Layer Pattern, Event-Based Architecture
- **Speech Recognition & Dictation:** Whisper and Gemini-based transcription with hotkey support
- **Docker Support:** Dev (live reload), production, and lightweight deployments

## Core Architecture

### Multi-API Provider System
5-tier intelligent fallback with health monitoring:
1. **Claude Anthropic API** (primary, paid, high quality)
2. **Claude OAuth** (secondary, free, authenticated)
3. **Gemini API** (tertiary, Google AI)
4. **Ollama Local** (quaternary, localhost:11434)
5. **Ollama Remote** (final fallback, remote instances)

Provider selection based on: thermal conditions, request complexity, provider health, cost optimization, performance requirements.

### Key Components
- `src/mycoder/enhanced_mycoder_v2.py` (897 lines) - Main EnhancedMyCoderV2 class with multi-API integration
- `src/mycoder/api_providers.py` (1271 lines) - All provider implementations, APIProviderRouter for intelligent selection
- `src/mycoder/tool_registry.py` (707 lines) - FEI-inspired tool registry with execution contexts
- `src/mycoder/adaptive_modes.py` (671 lines) - Thermal-aware operational mode management
- `src/mycoder/config_manager.py` (602 lines) - Configuration management across providers
- `src/speech_recognition/` - Complete speech recognition and dictation module

## Project Structure & Module Organization

Core code lives in `src/mycoder/` (main class in `enhanced_mycoder_v2.py`, providers in `api_providers.py`, config in `config_manager.py`). The dictation app and speech tooling are under `src/speech_recognition/`. Tests live in `tests/` with `unit/`, `integration/`, `functional/`, `e2e/`, and `stress/` suites. Documentation is in `docs/` and runnable samples are in `examples/`. Root tooling includes `pyproject.toml`, `Makefile`, `Dockerfile*`, and `docker-compose*.yml`.

```
MyCoder-v2.0/
├── src/                          # Source code
│   ├── mycoder/                 # Core package
│   │   ├── enhanced_mycoder_v2.py   # Main class (897 lines)
│   │   ├── api_providers.py         # Providers & router (1271 lines)
│   │   ├── tool_registry.py         # Tool system (707 lines)
│   │   ├── adaptive_modes.py        # Thermal modes (671 lines)
│   │   ├── config_manager.py        # Config (602 lines)
│   │   └── cli.py                   # CLI interface
│   └── speech_recognition/      # Dictation module
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── functional/              # Functional tests
│   ├── e2e/                     # End-to-end tests
│   └── stress/                  # Stress & thermal tests
├── docs/                        # Documentation
├── examples/                    # Usage examples
└── Makefile                     # Development automation (Czech)
```

## Development Commands

### Installation
```bash
# Poetry (recommended)
poetry install                    # Basic install
poetry install --extras http     # With HTTP features
poetry install --extras speech   # With speech recognition

# Without Poetry
pip install -r requirements.txt
```

### CLI Commands (Poetry Scripts)
```bash
poetry run mycoder               # Interactive MyCoder CLI
poetry run mycoder-demo          # Run demo
poetry run dictation             # Launch speech recognition/dictation
```

### Testing
```bash
# Unit tests
poetry run pytest tests/unit/ -v

# Integration tests
poetry run pytest tests/integration/ -v

# Functional tests
poetry run pytest tests/functional/ -v

# E2E tests
poetry run pytest tests/e2e/ -v

# Stress tests
python tests/stress/run_stress_tests.py --all
python tests/stress/run_stress_tests.py --quick
python tests/stress/run_stress_tests.py --suite thermal  # Requires Q9550

# By marker
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m thermal      # Q9550 only
poetry run pytest -m network      # Network required
poetry run pytest -m "not thermal"  # Skip thermal tests
```

### Docker Development (Czech Makefile)
```bash
# Development
make dev              # Start dev server with live reload
make dev-detached     # Start in background
make dev-shell        # Open shell in container
make dev-python       # Python shell in dev environment

# Production
make prod             # Start production server
make prod-detached    # Production in background

# Lightweight (2-4GB RAM, TinyLlama)
make light            # Ultra-lightweight version
make light-detached   # Lightweight in background

# Testing & Quality
make test             # Run tests in Docker
make test-integration # Integration tests
make test-quick       # Quick smoke tests
make lint             # Run linting
make format           # Format code

# Container Management
make logs             # View dev logs
make logs-prod        # View production logs
make status           # Show service status
make health           # Health check
make stop             # Stop all services
make clean            # Clean Docker cache

# Build
make build-dev        # Rebuild dev image
make build-prod       # Rebuild production image

# Local Python (without Docker)
make venv             # Create venv, install via Poetry
make test-local       # Run tests locally
make lint-local       # Lint locally
make format-local     # Format locally
```

### Code Quality
```bash
# Format code
poetry run black . && poetry run isort .

# Linting
poetry run flake8 src/ tests/

# Type checking (strict mode enabled)
poetry run mypy src/
```

## Testing Framework

### Test Categories
- **Unit** (`tests/unit/`) - Core component functionality
- **Integration** (`tests/integration/`) - Real API interactions
- **Functional** (`tests/functional/`) - End-to-end workflows
- **E2E** (`tests/e2e/`) - Simulation-based end-to-end
- **Stress** (`tests/stress/`) - System limits and thermal management

### Test Markers (pyproject.toml)
- `unit` - Unit tests
- `integration` - Integration tests
- `functional` - Functional tests
- `stress` - Stress tests
- `performance` - Performance tests
- `slow` - Slow running tests
- `network` - Requires network access
- `thermal` - Requires Q9550 thermal system
- `auth` - Requires Claude CLI authentication

### Test Conventions
- File naming: `test_*.py` or `*_test.py`
- Function naming: `test_*`
- Test classes: `Test*`
- Coverage target: 85%+ for new features

## Configuration Management

### Environment Variables
```bash
# API Keys
export ANTHROPIC_API_KEY="your_anthropic_key"
export GEMINI_API_KEY="your_gemini_key"

# System Configuration
export MYCODER_DEBUG=1
export MYCODER_THERMAL_MAX_TEMP=75
export MYCODER_PREFERRED_PROVIDER=claude_oauth
```

### Configuration Files
- **`mycoder_config.json`** - Main configuration for all providers
- **`pyproject.toml`** - Project settings, dependencies, tool configs (Black, isort, mypy, pytest)
- **`docker-compose*.yml`** - Three deployment modes (dev, prod, lightweight)
- **`dictation_config_local.json`** - Speech recognition configuration

## Q9550 Thermal Management

### Features
- **Temperature Monitoring:** Real-time CPU temperature tracking
- **Automatic Throttling:** Reduces AI workload when temp > 75°C
- **Emergency Protection:** Hard shutdown at 85°C
- **PowerManagement Integration:** Uses existing thermal scripts at `/home/milhy777/Develop/Production/PowerManagement/`

### Thermal Testing
```bash
# Full thermal stress testing (requires Q9550)
python tests/stress/run_stress_tests.py --suite thermal

# Skip thermal tests on non-Q9550 systems
poetry run pytest -m "not thermal"
```

## Speech Recognition Module

The `src/speech_recognition/` module provides comprehensive dictation and voice command capabilities.

### Components
- `cli.py` - Command-line interface (accessible via `poetry run dictation`)
- `dictation_app.py` - Main dictation application
- `whisper_transcriber.py` - OpenAI Whisper-based transcription
- `gemini_transcriber.py` - Google Gemini-based transcription
- `audio_recorder.py` - Audio capture and processing
- `hotkey_manager.py` - Keyboard shortcut management
- `text_injector.py` - Text insertion into applications
- `overlay_button.py` - UI overlay for dictation control
- `setup_wizard.py` - Initial configuration wizard

### Usage
```bash
# Launch dictation system
poetry run dictation

# Install with speech dependencies
poetry install --extras speech
```

## API Provider System

### Provider Priority Logic
Intelligent selection based on:
1. **Thermal conditions** - Prefer local inference when CPU temp > 70°C
2. **Request complexity** - Route complex tasks to more capable providers
3. **Provider health** - Skip unhealthy providers in fallback chain
4. **Cost optimization** - Prefer free/cheaper options when appropriate
5. **Performance requirements** - Balance speed vs quality based on context

### Provider Configuration
Each provider can be configured in `mycoder_config.json` with:
- `enabled` - Enable/disable provider
- `timeout_seconds` - Request timeout
- `max_retries` - Retry attempts
- `model` - Model selection (where applicable)

## Coding Style & Naming Conventions

Python 3.10-3.13, 4-space indent. Format with Black (see `pyproject.toml`), lint with flake8, and install hooks via `pre-commit install`. Use type hints and docstrings for public APIs.

**Naming:**
- `snake_case` for functions/variables
- `PascalCase` for classes
- `UPPER_SNAKE` for constants

Keep configuration in JSON and environment variables, not hard-coded.

## Security & Configuration Tips

Never commit API keys; use env vars like `ANTHROPIC_API_KEY` and `GEMINI_API_KEY`. Project config can live in `mycoder_config.json`. In containers, consider disabling thermal controls with `MYCODER_THERMAL_ENABLED=false` unless sensors are available.

## Commit & Pull Request Guidelines

History mixes conventional commits and short imperative subjects; prefer `feat:`/`fix:` (optional scope) and keep messages concise. PRs should include a summary, tests run, documentation updates, and a linked issue if applicable. Note any config/env changes (e.g., `MYCODER_PREFERRED_PROVIDER`) and include sample output/logs for behavior changes.

## Hardware Profiles

### MiniPC (ssh `MiniPC`)
- **OS:** Debian GNU/Linux 12 (bookworm), 32-bit (`i686`)
- **CPU:** Intel Atom N280 @ 1.66 GHz (1 core / 2 threads)
- **RAM:** 2.0 GiB (swap 3.0 GiB)
- **Storage:** 119 GB SSD/HDD (`/dev/sda1`, ~62 GB free)
- **GPU:** Intel 945GSE integrated
- **Recommended workflow:** Use `mycoder_config_minipc_32bit.json` (copy to `mycoder_config.json`), prefer local `venv` + `poetry install --extras http`, run `pytest tests/unit -v -m "not thermal"`, avoid Docker and stress/thermal tests on this host

### Q9550 Development System
- **CPU:** Intel Core 2 Quad Q9550 @ 2.83GHz (4 cores)
- **Thermal Monitoring:** Enabled, max temp 75°C, critical 85°C
- **RAM:** 4GB+ recommended for full test suite
- **Use for:** Thermal testing, stress testing, full development workflow

## Performance Benchmarks

On Q9550 @ 2.83GHz:
- **Simple Query:** 0.5-2.0s (Claude OAuth, cached auth)
- **File Analysis:** 2.0-5.0s (Ollama Local inference)
- **Complex Task:** 5.0-15.0s (Claude Anthropic API)
- **Thermal Check:** <0.1s (Q9550 sensors, hardware direct)

## Troubleshooting

### Common Issues
- **Thermal tests failing:** Ensure Q9550 system with PowerManagement scripts
- **Provider timeouts:** Check API keys and network connectivity
- **Memory errors:** Ensure 4GB+ RAM for full test suite
- **Docker build issues:** Use `make clean` then rebuild
- **Live reload not working:** Check mounted volumes: `docker-compose -f docker-compose.dev.yml config | grep -A5 volumes`

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

---

**Project emphasizes:** Production reliability, thermal safety for Q9550 systems, and comprehensive testing across multiple AI providers.
