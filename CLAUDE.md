# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MyCoder-v2.0 is a production-ready AI development assistant with a 5-tier API provider fallback system, Intel Q9550 thermal management, and FEI-inspired architecture. This is a Poetry-managed Python project with comprehensive testing and Docker support.

## Core Architecture

### Multi-API Provider System
- **5-tier fallback**: Claude Anthropic API → Claude OAuth → Gemini → Ollama Local → Ollama Remote  
- **Provider router**: `src/api_providers.py` handles intelligent provider selection
- **Thermal awareness**: Integrated Q9550 temperature monitoring affects provider selection

### Key Components
- **`src/enhanced_mycoder_v2.py`**: Main EnhancedMyCoderV2 class with multi-API integration
- **`src/api_providers.py`**: All API provider implementations and routing logic
- **`src/tool_registry.py`**: FEI-inspired tool registry with execution contexts  
- **`src/adaptive_modes.py`**: Thermal-aware operational mode management
- **`src/config_manager.py`**: Configuration management across providers

## Development Commands

### Project Setup
```bash
# Install dependencies
poetry install

# Install with extras for HTTP features
poetry install --extras http
```

### Testing Framework
```bash
# Unit tests (core functionality)
poetry run pytest tests/unit/ -v

# Integration tests (API interactions) 
poetry run pytest tests/integration/ -v

# Functional tests (end-to-end workflows)
poetry run pytest tests/functional/ -v

# Stress tests (system limits and Q9550 thermal)
python tests/stress/run_stress_tests.py --all
python tests/stress/run_stress_tests.py --quick     # Fast suites only
python tests/stress/run_stress_tests.py --suite thermal  # Requires Q9550
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

### Docker Development
```bash
# Development with live reload
make dev

# Production deployment
make prod

# Lightweight version (for limited resources)
make light

# Container shell access
make dev-shell

# View logs
make logs
```

### Makefile Quick Commands
The project includes a comprehensive Czech-language Makefile with shortcuts:
- `make dev` - Development server with live reload
- `make test` - Run tests in container
- `make format` - Code formatting
- `make status` - Show service status  
- `make health` - Health check all services

## Test Structure and Markers

### Test Categories
- **Unit tests** (`tests/unit/`): Core component functionality (85% pass rate target)
- **Integration tests** (`tests/integration/`): Real API interactions (90% pass rate)  
- **Functional tests** (`tests/functional/`): End-to-end workflows (95% pass rate)
- **Stress tests** (`tests/stress/`): System limits and thermal management (80% pass rate)

### Test Markers
```bash
# Run specific test types
poetry run pytest -m unit
poetry run pytest -m integration  
poetry run pytest -m thermal      # Requires Q9550 system
poetry run pytest -m network      # Requires network access
poetry run pytest -m auth         # Requires Claude CLI auth
```

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
- **`pyproject.toml`**: Project settings, dependencies, tool configurations
- **`docker-compose*.yml`**: Three deployment modes (dev, prod, lightweight)

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
python tests/stress/run_stress_tests.py --all --no-thermal
```

## Package Structure

```
MyCoder-v2.0/
├── src/
│   ├── enhanced_mycoder_v2.py     # Main class with 5-tier API system
│   ├── api_providers.py           # Provider implementations and router
│   ├── tool_registry.py           # FEI-inspired tool system
│   ├── adaptive_modes.py          # Thermal-aware modes
│   ├── config_manager.py          # Configuration management
│   └── cli.py                     # Command-line interface
├── tests/
│   ├── unit/                      # Unit tests (85% coverage target)
│   ├── integration/               # API integration tests
│   ├── functional/                # End-to-end tests
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
1. **Implement provider**: Extend base provider class in `src/api_providers.py`
2. **Update router**: Add provider to routing logic
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
2. **Register tool**: Add to tool registry in `src/tool_registry.py`
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
poetry run python -m enhanced_mycoder_v2

# Pytest with detailed output
poetry run pytest tests/unit/ -v -s --tb=long

# Docker debug shell
make dev-shell
```

This project emphasizes production reliability, thermal safety for Q9550 systems, and comprehensive testing across multiple AI providers.