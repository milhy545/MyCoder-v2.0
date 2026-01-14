# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Note:** Also check `AGENTS.md` for latest project updates and shared context written by all AI agents (Claude, Jules/Gemini, Codex). When you make significant changes, document them in AGENTS.md's "Recent Changes" section.

## Project Overview

MyCoder v2.1.0 is a production-ready AI development assistant featuring **5-tier API provider fallback** (Claude Anthropic → Claude OAuth → Gemini → Ollama Local → Ollama Remote), **Q9550 thermal management**, and **FEI-inspired architecture**. Built with Python 3.10-3.13, managed via Poetry.

## Core Architecture

### Multi-API Provider System with Thermal Awareness

The system intelligently routes requests through a 5-tier fallback chain based on:
1. **Thermal conditions** - CPU temp > 70°C → prefer local inference (Ollama); 85°C → emergency shutdown
2. **Request complexity** - Complex tasks → more capable providers (Claude/Gemini)
3. **Provider health** - Real-time health checks skip unhealthy providers
4. **Cost optimization** - Prefer free/cheaper options when appropriate
5. **Performance requirements** - Balance speed vs quality based on context

**Request Flow:**
`EnhancedMyCoderV2.process_request()` → `APIProviderRouter.select_provider()` (analyzes thermal + complexity + health) → Attempt providers in priority order with automatic fallback → Thermal monitoring can force local-only or emergency shutdown

### Key Components & Patterns

- **`src/mycoder/enhanced_mycoder_v2.py`** (897 lines) - Main orchestrator managing provider selection and request processing
- **`src/mycoder/api_providers.py`** (1271 lines) - All provider implementations + APIProviderRouter with health checks and thermal integration
- **`src/mycoder/tool_registry.py`** (707 lines) - FEI-inspired: centralized tool management with execution contexts, permissions, sandboxing
- **`src/mycoder/adaptive_modes.py`** (671 lines) - Thermal-aware modes that adjust behavior to protect Q9550 hardware
- **`src/mycoder/config_manager.py`** (602 lines) - Unified configuration across all providers with validation
- **`src/speech_recognition/`** - Complete dictation module with Whisper/Gemini transcription, hotkey management, audio recording

**FEI-Inspired Patterns:**
- Tool Registry Pattern (centralized tool management with execution contexts)
- Service Layer Pattern (clean separation: API providers vs business logic)
- Event-Based Architecture (reactive system with health monitoring and thermal hooks)

## Development Commands

### Project Setup
```bash
poetry install                    # Basic install
poetry install --extras http     # With HTTP features
poetry install --extras speech   # With speech recognition
pip install -r requirements.txt  # Fallback without Poetry
```

### CLI Commands
```bash
poetry run mycoder        # Interactive CLI
poetry run mycoder-demo   # Run demo
poetry run dictation      # Launch speech recognition
```

## New Commands (v2.1.1)

### Voice Commands
- `/voice start` - Start voice dictation (GUI overlay)
- `/voice stop` - Stop voice dictation
- `/voice status` - Dictation status
- `/speak <text>` - Text-to-speech playback

### Provider Control
- `/provider <name>` - Override provider selection
  - Available: claude_anthropic, claude_oauth, gemini, mercury,
    ollama_local, termux_ollama, ollama_remote

## New Features (v2.1.1)

### Speech Recognition & TTS
- Voice dictation as MyCoder tool
- Text-to-speech AI response reading
- Czech language support
- Multi-backend TTS (pyttsx3, espeak, gtts, gemini)

### 7-Tier API Provider Fallback
1. Claude Anthropic (primary)
2. Claude OAuth (subscription)
3. Gemini (Google AI)
4. Mercury (Inception Labs diffusion LLM)
5. Ollama Local (thermal-aware)
6. Termux Ollama (Android device)
7. Ollama Remote (configured URLs)

### Smart Dynamic UI
- Progress bars for long operations
- Real-time provider health dashboard
- Thermal alerts with automatic throttling
- Token cost estimates

### Testing
```bash
# By test category
poetry run pytest tests/unit/ -v          # Unit tests
poetry run pytest tests/integration/ -v   # Integration tests
poetry run pytest tests/functional/ -v    # Functional tests
poetry run pytest tests/e2e/ -v           # E2E tests

# Stress tests (system limits and thermal)
python tests/stress/run_stress_tests.py --all
python tests/stress/run_stress_tests.py --quick
python tests/stress/run_stress_tests.py --suite thermal  # Requires Q9550

# By marker
poetry run pytest -m unit
poetry run pytest -m thermal           # Q9550 only
poetry run pytest -m "not thermal"     # Skip thermal tests
```

### Code Quality
```bash
poetry run black . && poetry run isort .  # Format
poetry run flake8 src/ tests/             # Lint
poetry run mypy src/                      # Type check (strict mode)
```

### Docker Development (Czech Makefile)

**Important:** Development mode uses bind mounts for live reload - code changes in `src/` appear instantly without container rebuild. Only rebuild when modifying `pyproject.toml`, Dockerfile, or system dependencies.

```bash
# Development with live reload (NO REBUILDS for code changes)
make dev / make dev-detached    # Start dev server (foreground/background)
make dev-shell / make dev-python # Open bash/Python shell in container

# Production and lightweight deployments
make prod / make prod-detached  # Production server
make light / make light-detached # Lightweight (2-4GB RAM, TinyLlama)

# Testing and quality in Docker
make test / make test-integration / make test-quick
make lint / make format

# Container management
make logs / make logs-prod / make status / make health
make stop / make restart / make clean

# Build and local development
make build-dev / make build-prod / make rebuild
make venv / make test-local / make lint-local / make format-local
```

## Test Structure

**Categories:** `tests/unit/` (core functionality), `tests/integration/` (API interactions), `tests/functional/` (end-to-end), `tests/e2e/` (simulation-based), `tests/stress/` (system limits + thermal)

**Markers:** `unit`, `integration`, `functional`, `stress`, `performance`, `slow`, `network`, `thermal` (Q9550 required), `auth` (Claude CLI auth required)

## Configuration

### Environment Variables
```bash
export ANTHROPIC_API_KEY="your_key"
export GEMINI_API_KEY="your_key"
export MYCODER_DEBUG=1
export MYCODER_THERMAL_MAX_TEMP=75
export MYCODER_PREFERRED_PROVIDER=claude_oauth
```

### Key Files
- `mycoder_config.json` - Main configuration for all providers
- `mycoder_config_minipc_32bit.json` - Optimized for Intel Atom 32-bit systems
- `pyproject.toml` - Project settings, dependencies, tool configs
- `docker-compose*.yml` - Three deployment modes (dev, prod, lightweight)
- `dictation_config_local.json` - Speech recognition configuration

## Q9550 Thermal Management

Real-time CPU temperature tracking with automatic throttling (>75°C reduces workload, 85°C emergency shutdown). Integrates with PowerManagement scripts at `/home/milhy777/Develop/Production/PowerManagement/`.

**Testing:** `python tests/stress/run_stress_tests.py --suite thermal` (requires Q9550 hardware)

## Hardware Profiles

### MiniPC (ssh `MiniPC`)
Debian 12 (32-bit i686), Intel Atom N280 @ 1.66 GHz (1 core/2 threads), 2GB RAM, 3GB swap, 62GB free storage. Use `mycoder_config_minipc_32bit.json`, run `poetry install --extras http`, avoid Docker, skip thermal/stress tests.

### Q9550 Development System
Intel Core 2 Quad Q9550 @ 2.83GHz (4 cores), thermal monitoring enabled (max 75°C, critical 85°C), 4GB+ RAM recommended. Use for thermal testing, stress testing, full development workflow.

## Performance Benchmarks (Q9550 @ 2.83GHz)
- Simple Query: 0.5-2.0s (Claude OAuth, cached auth)
- File Analysis: 2.0-5.0s (Ollama Local inference)
- Complex Task: 5.0-15.0s (Claude Anthropic API)
- Thermal Check: <0.1s (Q9550 sensors, hardware direct)

## Adding API Providers

1. Extend `BaseAPIProvider` class in `src/mycoder/api_providers.py`
2. Add provider to `APIProviderRouter` routing logic
3. Create unit and integration tests
4. Add provider configuration schema to config system

## Troubleshooting

**Common Issues:**
- Thermal tests failing → Ensure Q9550 system with PowerManagement scripts at `/home/milhy777/Develop/Production/PowerManagement/`
- Provider timeouts → Check API keys (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) and network connectivity
- Memory errors → Ensure 4GB+ RAM for full test suite; use lightweight profile for constrained systems
- Docker build issues → Run `make clean` then rebuild
- Live reload not working → Check mounted volumes: `docker-compose -f docker-compose.dev.yml config | grep -A5 volumes`

**Debug Mode:**
```bash
export MYCODER_DEBUG=1
poetry run python -m mycoder.enhanced_mycoder_v2       # Enable debug logging
poetry run pytest tests/unit/ -v -s --tb=long          # Detailed pytest output
make dev-shell                                         # Docker debug shell
```
