# Repository Guidelines

## Project Structure & Module Organization
Core code lives in `src/` (main class in `enhanced_mycoder_v2.py`, providers in `api_providers.py`, config in `config_manager.py`). The dictation app and speech tooling are under `src/speech_recognition/`. Tests live in `tests/` with `unit/`, `integration/`, `functional/`, and `stress/` suites. Documentation is in `docs/` and runnable samples are in `examples/`. Root tooling includes `pyproject.toml`, `Makefile`, `Dockerfile*`, and `docker-compose*.yml`.

## Build, Test, and Development Commands
- `make dev`: start dev container with live reload.
- `make dev-shell`: open a shell inside the dev container.
- `make test`: run pytest in the dev container.
- `make test-quick`: fast smoke tests.
- `make lint` / `make format`: flake8 and black.
- Local runs: `python -m pytest tests/ -v`.

## Coding Style & Naming Conventions
Python 3.8+, 4-space indent. Format with Black (see `pyproject.toml`), lint with flake8, and install hooks via `pre-commit install`. Use type hints and docstrings for public APIs. Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE` for constants. Keep configuration in JSON and environment variables, not hard-coded.

## Testing Guidelines
Pytest with pytest-asyncio is the standard. File naming: `test_*.py` or `*_test.py`; functions `test_*`. Markers include `unit`, `integration`, `functional`, `stress`. Aim for 85%+ coverage for new features. Examples: `python -m pytest tests/unit/ -v`, `python tests/stress/run_stress_tests.py --quick`.

## Commit & Pull Request Guidelines
History mixes conventional commits and short imperative subjects; prefer `feat:`/`fix:` (optional scope) and keep messages concise. PRs should include a summary, tests run, documentation updates, and a linked issue if applicable. Note any config/env changes (e.g., `MYCODER_PREFERRED_PROVIDER`) and include sample output/logs for behavior changes.

## Security & Configuration Tips
Never commit API keys; use env vars like `ANTHROPIC_API_KEY` and `GEMINI_API_KEY`. Project config can live in `mycoder_config.json`. In containers, consider disabling thermal controls with `MYCODER_THERMAL_ENABLED=false` unless sensors are available.

## MiniPC Hardware Profile (ssh `MiniPC`)
- OS: Debian GNU/Linux 12 (bookworm), 32-bit (`i686`)
- CPU: Intel Atom N280 @ 1.66 GHz (1 core / 2 threads)
- RAM: 2.0 GiB (swap 3.0 GiB)
- Storage: 119 GB SSD/HDD (`/dev/sda1`, ~62 GB free)
- GPU: Intel 945GSE integrated
- Recommended workflow: prefer local `venv` + `pytest tests/unit -v --skip-thermal`, avoid Docker and stress/thermal tests on this host.
