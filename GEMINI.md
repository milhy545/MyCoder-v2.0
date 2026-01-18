# GEMINI.md: Project Overview - Enhanced MyCoder v2.2.0

**Note:** Also check `AGENTS.md` for latest project updates and shared context written by all AI agents (Claude, Jules/Gemini, Codex). When you make significant changes, document them in AGENTS.md's "Recent Changes" section.

## Project Overview

Enhanced MyCoder v2.2.0 is a robust, production-ready AI development assistant designed for high availability, performance, and thermal safety. It features a sophisticated 7-tier API provider fallback system, unique thermal management tailored for Intel Q9550 processors, and a modular architecture inspired by Federated Event Infrastructure (FEI) patterns. The project is primarily developed in Python, leveraging Docker for consistent environments and a comprehensive testing suite for reliability.

**Key Features:**

*   **7-Tier API Provider Fallback:** Intelligent routing and automatic failover across Claude Anthropic, Claude OAuth, Gemini, Mercury, Ollama (local and remote), and Termux Ollama based on health, cost, and performance.
*   **Q9550 Thermal Management:** Real-time CPU temperature monitoring, automatic throttling of AI workloads, and emergency shutdown for Intel Q9550 systems to prevent hardware damage.
*   **Modular (FEI-inspired) Architecture:** Utilizes a Tool Registry Pattern, Service Layer Pattern, and Event-Based Architecture for flexible and scalable development.
*   **Agent Orchestration:** Specialized agents (Explore, Plan, Bash, General) coordinated by an intelligent orchestrator.
*   **Self-Evolve System:** Automated test failure detection, patch generation, approval workflow, and dry-run sandbox.
*   **Circuit Breaker & Rate Limiting:** Resilient API provider management with automatic recovery to prevent cascade failures.
*   **Speech Recognition & Dictation:** Includes capabilities for voice commands and dictation through its `speech_recognition` module, leveraging technologies like Whisper.
*   **Activity Panel:** Dynamic UI for real-time monitoring of system status and agent activities.
*   **Docker Support:** Provides `docker-compose` configurations for development (with live reload), production, and lightweight deployments optimized for various hardware capabilities.

## Technologies Used

*   **Programming Language:** Python (3.10-3.13)
*   **Dependency Management:** Poetry (`pyproject.toml`)
*   **Containerization:** Docker, Docker Compose
*   **AI Providers:** Anthropic Claude, Google Gemini, Mercury (Inception Labs), Ollama (local/remote/Termux)
*   **Testing Frameworks:** Pytest (with `pytest-asyncio`, `pytest-cov`, `pytest-mock`)
*   **Code Quality Tools:** Black (code formatter), isort (import sorter), flake8 (linter), MyPy (static type checker)
*   **CLI Libraries:** `click`, `prompt-toolkit`, `rich`
*   **Logging:** `structlog`
*   **System Utilities:** `psutil`
*   **Optional UI/Audio:** PyQt5, sounddevice, numpy, openai-whisper, torch (for speech recognition features)

## Building and Running

The project offers multiple ways to build, run, and interact with the application, primarily through a powerful `Makefile` that orchestrates Docker Compose commands.

### Local Development (via `Makefile` & Docker Compose)

The recommended development workflow uses Docker Compose with live reloading, meaning changes to source code (`src/`) are reflected instantly without rebuilding containers.

*   **Start Development Environment:**
    ```bash
    make dev
    # Or: docker-compose -f docker-compose.dev.yml up
    ```
*   **Open Shell in Dev Container:**
    ```bash
    make dev-shell
    ```
*   **View Logs:**
    ```bash
    make logs
    ```
*   **Stop Services:**
    ```bash
    make stop
    ```

### Production Deployment (via `Makefile` & Docker Compose)

For a stable, optimized production environment.

*   **Start Production Environment:**
    ```bash
    make prod
    # Or: docker-compose up
    ```

### Lightweight Deployment (via `Makefile` & Docker Compose)

An optimized version for systems with limited resources (e.g., 2-4GB RAM).

*   **Start Lightweight Environment:**
    ```bash
    make light
    ```

### Local Python Installation (without Docker)

If you prefer to run MyCoder directly on your system.

*   **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    # Or using Poetry: poetry install
    ```
*   **Run MyCoder (Example):**
    ```python
    from mycoder import EnhancedMyCoderV2
    from pathlib import Path
    import asyncio

    config = {"ollama_local": {"enabled": True, "model": "tinyllama"}}
    mycoder = EnhancedMyCoderV2(working_directory=Path("."), config=config)
    asyncio.run(mycoder.initialize())
    response = asyncio.run(mycoder.process_request("What is Python?"))
    print(response['content'])
    ```

## Testing

The project includes a comprehensive test suite across different categories.

*   **Run All Tests (in Dev Container):**
    ```bash
    make test
    # Or locally: poetry run pytest tests/ -v
    ```
*   **Run Unit Tests:**
    ```bash
    poetry run pytest tests/unit/ -v
    ```
*   **Run Integration Tests:**
    ```bash
    poetry run pytest tests/integration/ -v
    ```
*   **Run Functional Tests:**
    ```bash
    poetry run pytest tests/functional/ -v
    ```
*   **Run Stress Tests:**
    ```bash
    python tests/stress/run_stress_tests.py --all
    # For Q9550 thermal stress tests: python tests/stress/run_stress_tests.py --suite thermal
    ```

## Development Conventions

### Code Style and Quality

*   **Python Version:** Compatible with Python 3.10-3.13.
*   **Formatting:** Follows Black formatting guidelines (`make format` or `poetry run black .`).
*   **Import Sorting:** `isort` for organizing imports.
*   **Linting:** `flake8` for code style enforcement (`make lint` or `poetry run flake8 src/ tests/`).
*   **Type Checking:** `mypy` is used for static type analysis (`poetry run mypy src/`).
*   **Pre-commit Hooks:** Recommended to install pre-commit hooks to automate quality checks (`pre-commit install`).
*   **Docstrings & Type Hints:** All public APIs should include comprehensive docstrings and type hints.

### Testing Practices

*   **Framework:** `pytest` is the standard testing framework, with `pytest-asyncio` for asynchronous code.
*   **Test File Naming:** `test_*.py` or `*_test.py`.
*   **Test Function Naming:** `test_*`.
*   **Test Markers:** Tests are categorized using markers like `unit`, `integration`, `functional`, `stress`, `thermal`, `network`, and `auth`.
*   **Coverage:** Aim for 85%+ code coverage for new features.

### Configuration Management

*   **API Keys:** Sensitive information like API keys should **never** be hardcoded or committed. Use environment variables (e.g., `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`).
*   **Project Configuration:** `mycoder_config.json` for main application settings.
*   **Environment Variables:** Extensive use of environment variables for dynamic configuration (e.g., `MYCODER_DEBUG`, `MYCODER_THERMAL_MAX_TEMP`).

### Project Structure (Key Directories)

```
MyCoder-v2.0/
├── src/                          # Main source code
│   ├── mycoder/                 # Core package
│   │   ├── enhanced_mycoder_v2.py   # Core MyCoder class
│   │   ├── api_providers.py         # API provider implementations and router
│   │   ├── config_manager.py        # Configuration handling
│   │   ├── tool_registry.py         # Tool management system
│   │   ├── adaptive_modes.py        # Adaptive mode logic (thermal, etc.)
│   │   ├── agents/                  # Agent orchestration (Explore, Plan, Bash, General)
│   │   ├── self_evolve/             # Self-evolution system
│   │   ├── mcp/                     # Model Context Protocol client
│   │   ├── tools/                   # Enhanced tools
│   │   ├── ui_activity_panel.py     # Activity Panel UI
│   │   ├── ui_dynamic_panels.py     # Dynamic UI components
│   │   ├── web_tools.py             # Web fetch/search tools
│   └── speech_recognition/      # Dictation and speech-related modules
├── tests/                       # Comprehensive test suites
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── functional/              # Functional tests
│   ├── e2e/                     # End-to-end simulation tests
│   └── stress/                  # Stress and thermal tests
├── docs/                        # Project documentation and guides
├── examples/                    # Code examples and demos
├── docker-compose*.yml          # Docker Compose configurations
├── Dockerfile*                  # Docker build files
├── Makefile                     # Development automation (Czech language)
└── pyproject.toml               # Poetry project configuration
```