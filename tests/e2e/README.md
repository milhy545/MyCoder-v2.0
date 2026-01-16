# AI E2E Testing

This directory contains the AI testing framework for MyCoder, including:

- `framework/` core simulator, scenario engine, assertions, metrics, reports
- `fixtures/` JSON scenario definitions and expected behaviors
- `scenarios/` scenario loader modules
- `runner.py` self-test runner with auto-iteration support

## Quick Start

Run the full E2E suite:

```bash
poetry run pytest tests/e2e/ -v
```

Run the self-test runner with reports:

```bash
poetry run python tests/e2e/runner.py --report --report-formats console,json,html,md
```

Use common scenarios instead of fixtures:

```bash
poetry run python tests/e2e/runner.py --source common --report --report-formats console
```

## Reports

Reports are written to `tests/e2e/reports/` and include:

- Console summary (stdout)
- JSON (`run_<timestamp>.json`)
- HTML (`run_<timestamp>.html`)
- Markdown (`run_<timestamp>.md`)

## Fixtures

`fixtures/test_prompts.json` groups scenarios by type:

- `prompt_engineering`
- `tool_selection`
- `context_awareness`
- `error_handling`

`fixtures/expected_behaviors.json` adds optional validation fields:

- `expected_steps`
- `expected_actions`
- `expected_context_keys`
- `expected_alternatives`
