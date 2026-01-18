# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Note:** Also check `AGENTS.md` for latest project updates and shared context written by all AI agents (Claude, Jules/Gemini, Codex). When you make significant changes, document them in AGENTS.md's "Recent Changes" section.

## Project Overview

MyCoder v2.2.0 is a production-ready AI development assistant featuring **7-tier API provider fallback** (Claude Anthropic → Claude OAuth → Gemini → Mercury → Ollama Local → Termux Ollama → Ollama Remote), **Q9550 thermal management**, **agent orchestration**, and **FEI-inspired architecture**. Built with Python 3.10-3.13, managed via Poetry.

## Core Architecture

### Multi-API Provider System with Thermal Awareness

The system intelligently routes requests through a 7-tier fallback chain based on:
1. **Thermal conditions** - CPU temp > 70°C → prefer local inference (Ollama); 85°C → emergency shutdown
2. **Request complexity** - Complex tasks → more capable providers (Claude/Gemini)
3. **Provider health** - Real-time health checks skip unhealthy providers
4. **Cost optimization** - Prefer free/cheaper options when appropriate
5. **Performance requirements** - Balance speed vs quality based on context

**Request Flow:**
`EnhancedMyCoderV2.process_request()` → `APIProviderRouter.select_provider()` (analyzes thermal + complexity + health) → Attempt providers in priority order with automatic fallback → Thermal monitoring can force local-only or emergency shutdown

### Key Components & Patterns

- **`src/mycoder/enhanced_mycoder_v2.py`** - Main orchestrator managing provider selection and request processing
- **`src/mycoder/api_providers.py`** - All provider implementations + APIProviderRouter with health checks, thermal integration, CircuitBreaker, RateLimiter
- **`src/mycoder/tool_registry.py`** - FEI-inspired: centralized tool management with execution contexts, permissions, sandboxing
- **`src/mycoder/adaptive_modes.py`** - Thermal-aware modes that adjust behavior to protect Q9550 hardware
- **`src/mycoder/config_manager.py`** - Unified configuration across all providers with validation
- **`src/mycoder/agents/`** - Agent orchestration (Explore, Plan, Bash, General-purpose)
- **`src/mycoder/self_evolve/`** - Self-evolution system with approval workflow, sandbox, risk assessment
- **`src/mycoder/mcp/`** - MCP (Model Context Protocol) client support
- **`src/mycoder/tools/`** - Enhanced edit tool with unique string validation
- **`src/mycoder/web_tools.py`** - Web fetch and search with caching
- **`src/mycoder/todo_tracker.py`** - Task tracking with JSON persistence
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

## Interactive CLI Commands

### Evolution Features (v2.2.0)
- `/todo` - Track and review pending tasks
- `/plan` - Generate/approve execution plans
- `/edit <file>` - Guided edit workflow with unique string validation
- `/agent` - Agent selection and orchestration (Explore, Plan, Bash, General-purpose)
- `/web` - Web fetch/search with caching
- `/mcp` - Connect/call MCP servers
- `/self-evolve` - Approval-gated self-evolution with dry-run sandbox
- `/init` - Generate project guide files (CLAUDE.md, README.md)

### Voice & Speech (v2.1.1)
- `/voice start` - Start voice dictation with GUI overlay
- `/voice stop` - Stop voice dictation
- `/voice status` - Check dictation status
- `/speak <text>` - Text-to-speech playback (Czech language support)

### Provider Control
- `/provider <name>` - Override provider selection
  - Available: claude_anthropic, claude_oauth, gemini, mercury, ollama_local, termux_ollama, ollama_remote

### Chat Management
- `/history` - View chat history
- `/scroll up/down` - Navigate chat history
- `/clear` - Clear chat history

## Key Features

### 7-Tier API Provider Fallback
1. **Claude Anthropic** - Primary (paid, high quality)
2. **Claude OAuth** - Secondary (subscription)
3. **Gemini** - Google AI
4. **Mercury** - Inception Labs diffusion LLM
5. **Ollama Local** - Thermal-aware local inference
6. **Termux Ollama** - Android device via WiFi/USB
7. **Ollama Remote** - Remote Ollama instances (final fallback)

### Smart Dynamic UI with Activity Panel
- Progress bars for long operations
- Real-time provider health dashboard
- Thermal alerts with automatic throttling
- Token cost estimates
- CPU/RAM/Temperature monitoring in Activity Panel
- Auto-execute flow with streaming callbacks
- Keyboard scrolling for chat history

### Resilience & Safety
- **Circuit Breaker** - Prevents cascade failures across providers
- **Rate Limiter** - Ensures API compliance
- **Thermal Management** - Q9550 CPU protection with automatic throttling
- **Self-Evolve System** - Automated test failure detection with approval workflow and sandbox testing

## Testing

### Running Tests

**CRITICAL:** Always use `poetry run pytest` - pytest is NOT in PATH without Poetry.

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

# Run specific test file
poetry run pytest -q tests/unit/test_xyz.py
```

### Test Structure

**Categories:** `tests/unit/` (core functionality), `tests/integration/` (API interactions), `tests/functional/` (end-to-end), `tests/e2e/` (simulation-based), `tests/stress/` (system limits + thermal)

**Markers:** `unit`, `integration`, `functional`, `stress`, `performance`, `slow`, `network`, `thermal` (Q9550 required), `auth` (Claude CLI auth required)

### Testing Protocol

**MANDATORY FOR ALL CHANGES:**
1. Write/modify code
2. Immediately run relevant tests: `poetry run pytest`
3. Show test results to user
4. Only then mark task as complete

### Code Quality
```bash
poetry run black . && poetry run isort .  # Format
poetry run flake8 src/ tests/             # Lint
poetry run mypy src/                      # Type check (strict mode)
```

## Docker Development (Czech Makefile)

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

## Critical Implementation Details

### File Edit Tool Flow
The file edit system requires specific sequencing:
1. Files must be read via `file_read` tool before editing
2. `EditTool.validate_edit()` normalizes both relative and absolute paths
3. `file_write` automatically marks files as read for immediate editing
4. Enhanced edit tool validates unique string matches to prevent ambiguous edits

**Bug History (v2.2.0):**
- Fixed: file_write now marks files as read via `on_read` callback
- Fixed: EditTool path normalization handles relative/absolute paths
- Fixed: Sequential edits work properly with working_directory context

### Auto-Execute Flow
The interactive CLI can auto-execute file operations:
- Parses responses for file_read/file_write/file_edit commands
- Streams execution with progress callbacks
- Activity Panel shows real-time CPU/RAM/TEMP metrics
- Keyboard scrolling (↑/↓) for chat history navigation

### Function Calling API Support
API providers (Claude Anthropic, Gemini) support Function Calling with tool schemas:
- Tool definitions exported from tool_registry
- Responses normalized (tool_use/functionCall → tool_calls)
- Edge cases: multiple tools, missing functionCall field handled
- Unit tests: `test_api_providers.py` covers function calling scenarios

## Thermal Management

Real-time CPU temperature tracking with automatic throttling (>75°C reduces workload, 85°C emergency shutdown). Configure thermal scripts path via `MYCODER_THERMAL_SCRIPT` env var or in `mycoder_config.json`.

**Testing:** `python tests/stress/run_stress_tests.py --suite thermal` (requires thermal sensors)

## Hardware Profiles

### Q9550 Development System
- CPU: Intel Core 2 Quad Q9550 @ 2.83GHz (4 cores)
- Thermal monitoring enabled
- Use for: Full development, thermal testing, stress testing

### MiniPC (32-bit Intel Atom)
For resource-constrained systems (32-bit, low RAM), use `mycoder_config_minipc_32bit.json`, run `poetry install --extras http`, avoid Docker, skip thermal/stress tests with `-m "not thermal"`.

## Performance Benchmarks
- Simple Query: 0.5-2.0s (Claude OAuth, cached auth)
- File Analysis: 2.0-5.0s (Ollama Local inference)
- Complex Task: 5.0-15.0s (Claude Anthropic API)
- Thermal Check: <0.1s (hardware sensors)

## Adding API Providers

1. Extend `BaseAPIProvider` class in `src/mycoder/api_providers.py`
2. Add provider to `APIProviderRouter` routing logic
3. Create unit and integration tests
4. Add provider configuration schema to config system
5. Update fallback chain priority in `select_provider()`

## CI/CD Integration

GitHub Actions workflow includes:
- Credential gating for tests requiring API keys
- Black/isort formatting checks
- Unit/integration test suites
- Coverage reporting

**Recent fixes (2026-01-18):**
- Resolved CI failures in `main` and `alert-autofix-6` branches
- Fixed log injection vulnerability (PR #42)
- All tests passing, CI pipeline GREEN

## Troubleshooting

**Common Issues:**
- Thermal tests failing → Ensure thermal sensors available and `MYCODER_THERMAL_SCRIPT` configured
- Provider timeouts → Check API keys (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) and network connectivity
- Memory errors → Ensure 4GB+ RAM for full test suite; use lightweight profile for constrained systems
- Docker build issues → Run `make clean` then rebuild
- Live reload not working → Check mounted volumes: `docker-compose -f docker-compose.dev.yml config | grep -A5 volumes`
- "pytest not in PATH" → Always use `poetry run pytest`

**Debug Mode:**
```bash
export MYCODER_DEBUG=1
poetry run python -m mycoder.enhanced_mycoder_v2       # Enable debug logging
poetry run pytest tests/unit/ -v -s --tb=long          # Detailed pytest output
make dev-shell                                         # Docker debug shell
```

## Recent Major Changes (v2.2.0)

- Released v2.2.0 with unified versioning across all components
- Fixed critical file_edit bugs (3 bugs) in sequential edit workflow
- Formatted all code with black/isort (314 tests passing)
- Added 7-tier API provider fallback (Mercury, Termux Ollama added)
- Implemented Activity Panel with CPU/RAM/TEMP monitoring
- Added auto-execute flow with streaming callbacks
- Integrated agent orchestration (Explore, Plan, Bash, General)
- Added self-evolve system with approval workflow and sandbox
- Implemented circuit breaker and rate limiter for API resilience
- Added MCP (Model Context Protocol) client support
- Created comprehensive E2E AI simulation testing framework
