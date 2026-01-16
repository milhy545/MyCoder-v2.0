# AI Testing Framework Usage Guide

This guide explains how to run the AI E2E tests and the self-test runner.

## Run the E2E test suite

```bash
poetry run pytest tests/e2e/ -v
```

## Run the self-test runner

Run all scenarios from fixtures:

```bash
poetry run python tests/e2e/runner.py --report --report-formats console,json,html,md
```

Run only tool selection scenarios:

```bash
poetry run python tests/e2e/runner.py --scenario-type tool_selection --report --report-formats console
```

## Auto-iteration mode

```bash
poetry run python tests/e2e/runner.py --auto-iterate --max-iterations 10 --target-pass-rate 0.95
```

## Scenario sources

Use fixture-driven scenarios (default):

```bash
poetry run python tests/e2e/runner.py --source fixtures
```

Use built-in common scenarios:

```bash
poetry run python tests/e2e/runner.py --source common
```

## Reports

Reports are stored in `tests/e2e/reports/`:

- `run_<timestamp>.json`
- `run_<timestamp>.html`
- `run_<timestamp>.md`
