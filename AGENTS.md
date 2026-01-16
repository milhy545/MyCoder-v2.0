# Repository Guidelines

**Note:** This is a collaborative file maintained by all AI agents working on this project (Claude Code, Jules/Gemini, Codex). When you make significant changes to the project, document them in the Recent Changes section below.

## Recent Changes & Updates
*Agents: Add entries here when making significant changes*
- 2026-01-16: Claude Code - Released MyCoder v2.2.0: Unified versioning, fixed critical file_edit bugs (3 bugs), formatted all code with black/isort, 314 tests passing, pushed to GitHub ✅
- 2026-01-16: Claude Code - Verified MyCoder editing works in practice: sequential edits, /read,/edit,/write commands all functional
- 2026-01-16: Codex - Rozsiril unit testy pro function calling edge-cases (vice tool calls, zadny functionCall) v API providerech
- 2026-01-16: Codex - Dopsal unit testy pro function calling tool_use/functionCall v Claude/Gemini providerech
- 2026-01-16: Codex - Pridal tool schemata pro file tools, pridal function calling v Claude/Gemini providerech a normalizaci cest v EditTool.validate_edit
- 2026-01-16: Claude Code - Fixed critical file_edit bugs: (1) file_write now marks files as read for immediate editing, (2) EditTool properly normalizes relative/absolute paths, (3) added on_read callback to file_write tool. All test_enhanced_mycoder_v2_tools.py tests now pass ✅
- 2026-01-16: Claude Code - Created TODO_FILE_EDIT_FIX.md with detailed implementation plan for Function Calling API support (Anthropic/Gemini tool schemas) and system prompt improvements
- 2026-01-16: Claude Code - Updated CLAUDE.md: fixed 5→7 tier fallback inconsistency, added missing v2.2.0 components (agents/, self_evolve/, mcp/, tools/, web_tools.py, todo_tracker.py), reorganized CLI commands section, added Activity Panel and Resilience & Safety features
- 2026-01-16: Codex - Pridal system prompt pro /edit a parsovani /read,/edit,/write v enhanced_mycoder_v2, plus unit testy pro _enhance_with_tools
- 2026-01-16: Codex - Restored CPU/RAM/TEMP line in Activity Panel, added /init confirmation handling without Live glitches, and auto-included AGENTS/guide files in prompt context
- 2026-01-16: Codex - Added /init command to generate project guide files (CLI hook, generator, tests)
- 2026-01-16: Codex - Fixed auto-execute file writes to honor working_directory, improved file_write reliability (mkdir parents, allow empty content), and broadened file parsing.
- 2026-01-16: Codex - Added Activity Panel + auto-execute flow, streaming callbacks, keyboard scroll, and new unit tests for UI parsing/execution
- 2026-01-15: Codex - Updated CLAUDE.md with Evolution CLI commands (/todo, /plan, /edit, /agent, /web, /mcp, /self-evolve)
- 2026-01-15: Codex - Adjusted retryable error handling to include rate limit failures
- 2026-01-15: Codex - Fixed tool registry reset, MCP collisions, request retries, and recovery compatibility to address test failures
- 2026-01-15: Codex - Added phase 6 test coverage (todo, circuit breaker, rate limiter, MCP client, plan mode, integration stubs)
- 2026-01-15: Codex - Added web fetch/search tools, MCP protocol/client modules, and CLI commands with unit tests
- 2026-01-15: Codex - Added agent orchestration modules and /agent CLI support with unit tests
- 2026-01-15: Codex - Integrated file_edit tool into registry/CLI and added command parser tests
- 2026-01-15: Codex - Added unit tests for Enhanced Edit Tool
- 2026-01-15: Codex - Added Plan mode commands and Enhanced Edit Tool scaffolding
- 2026-01-15: Codex - Note: before reporting completion, always run full test suite
- 2026-01-15: Codex - Added Self-Evolve approval + dry-run, ProposalStore locking/cleanup, circuit breaker + rate limiter + lightweight health check, and todo tracker + CLI support
- 2026-01-14: Codex - Implemented Phase 1 POC AI Testing Framework (simulator, scenario engine, POC tests, directories)
- 2026-01-14: Codex - Added Phase 2 AI Testing Framework components (assertion framework, metrics collector)
- 2026-01-14: Codex - Added Phase 3 AI Testing Framework runner + report generator
- 2026-01-14: Codex - Added E2E fixtures and scenario test suites (prompt/tool/context/error)
- 2026-01-14: Codex - Extended fixtures for thermal and provider fallback scenarios
- 2026-01-14: Codex - Expanded fixtures with additional prompt/tool/context/error scenarios
- 2026-01-14: Codex - Added extra fixture scenarios and extended file-write detection for .md
- 2026-01-14: Codex - Added scenario modules + fixture loader with validation hooks; runner now loads fixtures
- 2026-01-14: Codex - Added thermal/provider recommended_actions handling and expected_actions validation
- 2026-01-14: Codex - Added fixture validations for context/alternatives, expanded fixtures, and documented E2E README
- 2026-01-14: Codex - Completed AI testing docs and examples (USAGE_GUIDE + examples)
- 2026-01-14: Codex - Added fallback metadata fixtures and router tests
- 2026-01-15: Codex - Added Self-Evolve MVP modules and CLI integration
- 2026-01-15: Codex - Added self-evolve risk scoring, rollback, issue-driven proposals, and monitoring logs
- 2026-01-14: Codex - Improved provider fallback logic with retries, metadata, and fallback_enabled
- 2026-01-14: Codex - Fixed runner UTC warning and tuned simulator for update dependencies in multi-step
- 2026-01-14: Codex - Renamed TestScenario to ScenarioDefinition to avoid pytest collection warnings
- 2026-01-14: Codex - Fixed multi-step detection to avoid comma-only false positives
- 2026-01-13: Codex - Added chat history persistence/scrolling commands and file-write verification with MCP response normalization
- 2026-01-13: Codex - Implemented v2.1.1 Phase 2/3: speech tool + TTS engine, Termux provider, dynamic UI, CLI voice/TTS commands, config updates, and tests
- 2026-01-08: Claude Code - Expanded AGENTS.md to serve as comprehensive shared context for all AI agents
- 2026-01-08: Claude Code - Created CLAUDE.md with detailed Claude Code-specific workflows
- 2026-01-08: Claude Code - Updated GEMINI.md with reference to AGENTS.md
- 2026-01-13: Codex - Fixed GitHub Actions workflow credential gating to avoid workflow file errors
- 2026-01-13: Codex - Updated filelock and virtualenv to address open Dependabot alerts
- 2026-01-13: Codex - Moved core modules into `src/mycoder`, updated imports/entrypoints/docs, added MiniPC 32-bit profile config+guide, and added public API unit test

## Project Overview

**Enhanced MyCoder v2.2.0** is a production-ready AI development assistant designed for high availability, performance, and thermal safety. Built with Python 3.10-3.13, managed via Poetry.

**Key Features:**
- **7-Tier API Provider Fallback:** Claude Anthropic → Claude OAuth → Gemini → Mercury → Ollama Local → Termux Ollama → Ollama Remote
- **Q9550 Thermal Management:** Real-time CPU temperature monitoring, automatic throttling, emergency protection
- **FEI-Inspired Architecture:** Tool Registry Pattern, Service Layer Pattern, Event-Based Architecture
- **Agent Orchestration:** Explore, Plan, Bash, and General-purpose agents with intelligent task routing
- **Self-Evolve System:** Automated test failure detection, patch generation, approval workflow, and dry-run sandbox
- **Circuit Breaker & Rate Limiting:** Resilient API provider management with automatic recovery
- **Speech Recognition & Dictation:** Whisper and Gemini-based transcription with hotkey support
- **Docker Support:** Dev (live reload), production, and lightweight deployments

## Core Architecture

### Multi-API Provider System
7-tier intelligent fallback with health monitoring, circuit breaker, and rate limiting:
1. **Claude Anthropic API** (primary, paid, high quality)
2. **Claude OAuth** (secondary, free, authenticated)
3. **Gemini API** (tertiary, Google AI)
4. **Mercury** (Inception Labs diffusion LLM)
5. **Ollama Local** (thermal-aware, localhost:11434)
6. **Termux Ollama** (Android device via WiFi/USB)
7. **Ollama Remote** (final fallback, remote instances)

Provider selection based on: thermal conditions, request complexity, provider health, cost optimization, performance requirements. Circuit breaker pattern prevents cascade failures, rate limiter ensures API compliance.

### Key Components
- `src/mycoder/enhanced_mycoder_v2.py` - Main EnhancedMyCoderV2 class with multi-API integration
- `src/mycoder/api_providers.py` - All provider implementations, APIProviderRouter, CircuitBreaker, RateLimiter
- `src/mycoder/tool_registry.py` - FEI-inspired tool registry with execution contexts
- `src/mycoder/adaptive_modes.py` - Thermal-aware operational mode management
- `src/mycoder/config_manager.py` - Configuration management across providers
- `src/mycoder/agents/` - Agent orchestration (Explore, Plan, Bash, General)
- `src/mycoder/self_evolve/` - Self-evolution system (proposals, risk assessment, sandbox, approval workflow)
- `src/mycoder/mcp/` - MCP (Model Context Protocol) client support
- `src/mycoder/tools/` - Enhanced edit tool with unique string validation
- `src/mycoder/web_tools.py` - Web fetch and search with caching
- `src/mycoder/todo_tracker.py` - Task tracking with JSON persistence
- `src/speech_recognition/` - Complete speech recognition and dictation module

## Project Structure & Module Organization

Core code lives in `src/mycoder/` (main class in `enhanced_mycoder_v2.py`, providers in `api_providers.py`, config in `config_manager.py`). The dictation app and speech tooling are under `src/speech_recognition/`. Tests live in `tests/` with `unit/`, `integration/`, `functional/`, `e2e/`, and `stress/` suites. Documentation is in `docs/` and runnable samples are in `examples/`. Root tooling includes `pyproject.toml`, `Makefile`, `Dockerfile*`, and `docker-compose*.yml`.

```
MyCoder-v2.0/
├── src/                          # Source code
│   ├── mycoder/                 # Core package
│   │   ├── enhanced_mycoder_v2.py   # Main class
│   │   ├── api_providers.py         # Providers, router, circuit breaker, rate limiter
│   │   ├── tool_registry.py         # Tool system
│   │   ├── adaptive_modes.py        # Thermal modes
│   │   ├── config_manager.py        # Config
│   │   ├── cli_interactive.py       # Interactive CLI
│   │   ├── agents/                  # Agent orchestration
│   │   │   ├── orchestrator.py      # Agent selection & execution
│   │   │   ├── explore.py           # Codebase exploration
│   │   │   ├── plan.py              # Implementation planning
│   │   │   ├── bash.py              # Command execution
│   │   │   └── general.py           # General-purpose agent
│   │   ├── self_evolve/             # Self-evolution system
│   │   │   ├── manager.py           # Orchestrator with approval workflow
│   │   │   ├── sandbox.py           # Git worktree dry-run
│   │   │   ├── risk_assessor.py     # Diff risk scoring
│   │   │   └── storage.py           # Proposals with filelock
│   │   ├── mcp/                     # MCP support
│   │   │   ├── client.py            # MCP client
│   │   │   └── protocol.py          # MCP protocol definitions
│   │   ├── tools/                   # Enhanced tools
│   │   │   └── edit_tool.py         # Unique string validation
│   │   ├── web_tools.py             # Web fetch/search with cache
│   │   └── todo_tracker.py          # Task tracking
│   └── speech_recognition/      # Dictation module
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests (290+ tests)
│   ├── integration/             # Integration tests
│   ├── functional/              # Functional tests
│   ├── e2e/                     # End-to-end AI simulation tests
│   └── stress/                  # Stress & thermal tests
├── docs/                        # Documentation
├── examples/                    # Usage examples
└── Makefile                     # Development automation (Czech)
```

## Agent Workflow Rules

### Testing Protocol (POVINNÉ PRO VŠECHNY AGENTY)
**KRITICKÉ:** Před dokončením jakéhokoliv úkolu MUSÍŠ spustit relevantní testy!

```bash
# Projekt používá Poetry - pytest VŽDY spouštěj přes poetry run
poetry run pytest -q tests/unit/test_xyz.py   # Konkrétní test file
poetry run pytest -q tests/unit/ -v           # Všechny unit testy
poetry run pytest -m unit                     # Jen unit marked testy
```

**"pytest není v PATH" NENÍ výmluva!** Použij `poetry run pytest`.

Workflow:
1. Napiš/změň kód
2. ⚠️ OKAMŽITĚ spusť testy (poetry run pytest)
3. Ukáž výsledky uživateli
4. Teprve pak označ úkol za dokončený

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
