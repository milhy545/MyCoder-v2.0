# AI Testing Framework for MyCoder v2.1.1

## Overview

Self-contained E2E testing framework pro iterativní vývoj AI logiky, promptů a tool selection.
Umožňuje AI agentovi (Claude Code) samostatně testovat a iterovat změny bez lidského zásahu.

## Architecture

```
tests/e2e/
├── AI_TESTING_FRAMEWORK.md          # Tato dokumentace
├── framework/
│   ├── __init__.py
│   ├── ai_simulator.py              # Mock AI responses & behavior
│   ├── scenario_engine.py           # Test scenario definitions
│   ├── assertion_framework.py       # AI behavior assertions
│   ├── metrics_collector.py         # Performance & quality metrics
│   └── report_generator.py          # Test reports & visualizations
├── scenarios/
│   ├── __init__.py
│   ├── prompt_engineering.py        # Prompt testing scenarios
│   ├── tool_selection.py            # Tool choice validation
│   ├── context_awareness.py         # Context retention tests
│   ├── error_handling.py            # Error recovery scenarios
│   └── edge_cases.py                # Edge case handling
├── fixtures/
│   ├── mock_responses.json          # Pre-defined AI responses
│   ├── test_prompts.json            # Test prompt library
│   └── expected_behaviors.json      # Expected behavior definitions
├── test_ai_prompt_engineering.py    # Prompt optimization tests
├── test_ai_tool_selection.py        # Tool selection logic tests
├── test_ai_context_retention.py     # Context awareness tests
└── runner.py                        # Self-test runner with auto-iteration
```

## Key Components

### 1. AI Simulator (`ai_simulator.py`)

Mock AI responses pro testování bez real API calls:

```python
class AISimulator:
    """
    Simuluje AI chování pro testování.

    Features:
    - Deterministic responses pro reprodukci
    - Controllable "intelligence" level
    - Tool usage simulation
    - Context tracking
    """

    def simulate_response(self, prompt, context, intelligence_level="normal"):
        """
        Vrátí mock AI response založenou na prompt patterns.

        Args:
            prompt: User/system prompt
            context: Kontext konverzace
            intelligence_level: "low", "normal", "high", "optimal"

        Returns:
            Mock APIResponse s předvídatelným chováním
        """
```

### 2. Scenario Engine (`scenario_engine.py`)

Test scenario definitions a execution:

```python
class TestScenario:
    """
    Definice testovacího scénáře.

    Attributes:
        name: Název scénáře
        user_input: Vstup od uživatele
        expected_tools: Očekávané použité nástroje
        expected_outcome: Očekávaný výsledek
        context: Kontext pro test
        validation_rules: Pravidla pro validaci
    """

class ScenarioEngine:
    """
    Spouští test scenarios a validuje výsledky.

    Features:
    - Parametrizované scenarios
    - Context injection
    - Result validation
    - Performance tracking
    """
```

### 3. Assertion Framework (`assertion_framework.py`)

AI-specific assertions:

```python
class AIAssertions:
    """
    Assertions pro AI behavior validation.

    Examples:
        assert_tool_selected(result, "file_read")
        assert_context_retained(result, previous_context)
        assert_error_handled_gracefully(result)
        assert_response_quality(result, min_score=0.8)
        assert_prompt_followed(result, original_prompt)
    """
```

### 4. Metrics Collector (`metrics_collector.py`)

Sbírá metriky pro performance tracking:

```python
class MetricsCollector:
    """
    Tracking AI performance metrics.

    Metrics:
    - Tool selection accuracy
    - Context retention rate
    - Response quality score
    - Error recovery rate
    - Prompt adherence score
    """
```

## Test Scenarios

### Scenario 1: Prompt Engineering

**Cíl:** Ověřit, že AI správně interpretuje a následuje prompts

```python
scenarios = [
    {
        "name": "Simple file read",
        "input": "Read the config file",
        "expected_tools": ["file_read"],
        "expected_behavior": "Should identify file and read it"
    },
    {
        "name": "Complex multi-step task",
        "input": "Update dependencies and run tests",
        "expected_tools": ["bash", "file_read"],
        "expected_behavior": "Should break into steps: 1) poetry update 2) pytest"
    },
    {
        "name": "Ambiguous request",
        "input": "Fix the bug",
        "expected_behavior": "Should ask for clarification or analyze context"
    }
]
```

### Scenario 2: Tool Selection

**Cíl:** Validovat správný výběr nástrojů

```python
tool_selection_tests = [
    {
        "input": "What's in mycoder_config.json?",
        "correct_tool": "file_read",
        "wrong_tools": ["bash", "git", "mcp"],
        "reason": "Direct file read is most efficient"
    },
    {
        "input": "Show git history",
        "correct_tool": "bash",  # git log
        "alternatives": ["mcp"],  # if MCP has git integration
        "wrong_tools": ["file_read"],
    }
]
```

### Scenario 3: Context Awareness

**Cíl:** Ověřit, že AI si pamatuje kontext

```python
context_tests = [
    {
        "conversation": [
            {"user": "Let's work on api_providers.py", "ai_should_remember": "api_providers.py"},
            {"user": "Show me the TermuxOllamaProvider", "ai_should": "grep in api_providers.py"},
            {"user": "What's on line 1125?", "ai_should": "read api_providers.py:1125"}
        ]
    }
]
```

### Scenario 4: Error Handling

**Cíl:** Testovat recovery z chyb

```python
error_scenarios = [
    {
        "input": "Read nonexistent_file.txt",
        "expected_error": "File not found",
        "expected_recovery": "Ask user or suggest alternatives"
    },
    {
        "input": "Run invalid command: foobar123",
        "expected_error": "Command not found",
        "expected_recovery": "Suggest correct command or ask for clarification"
    }
]
```

## Self-Test Runner

**Automatický runner pro iterativní testování:**

```python
class SelfTestRunner:
    """
    Autonomous test runner for AI agents.

    Features:
    - Run all scenarios automatically
    - Collect metrics
    - Generate reports
    - Suggest improvements
    - Auto-iterate on failures
    """

    def run_iteration(self, scenarios):
        """Run one test iteration"""
        results = []
        for scenario in scenarios:
            result = self.execute_scenario(scenario)
            results.append(result)
        return results

    def analyze_results(self, results):
        """Analyze test results and suggest improvements"""
        failures = [r for r in results if not r.passed]

        # Generate improvement suggestions
        suggestions = self.generate_suggestions(failures)

        return {
            "pass_rate": len([r for r in results if r.passed]) / len(results),
            "failures": failures,
            "suggestions": suggestions
        }

    def auto_iterate(self, max_iterations=10):
        """
        Automatically iterate on improvements until pass rate > threshold.

        Process:
        1. Run tests
        2. Analyze failures
        3. Generate improvements
        4. Apply improvements
        5. Re-run tests
        6. Repeat until pass_rate > 0.95 or max_iterations
        """
```

## Usage Examples

### Example 1: Test Prompt Engineering

```bash
# Run prompt engineering tests
poetry run pytest tests/e2e/test_ai_prompt_engineering.py -v

# Run with detailed metrics
poetry run pytest tests/e2e/test_ai_prompt_engineering.py -v --collect-metrics

# Run auto-iteration mode (AI fixes failures automatically)
poetry run python tests/e2e/runner.py --auto-iterate --max-iterations 10
```

### Example 2: Validate Tool Selection

```bash
# Test tool selection logic
poetry run pytest tests/e2e/test_ai_tool_selection.py -v

# Generate tool selection report
poetry run python tests/e2e/runner.py --scenario tool_selection --report
```

### Example 3: Self-Test with Auto-Improvement

```python
# In Python script or Jupyter notebook
from tests.e2e.runner import SelfTestRunner

runner = SelfTestRunner()

# Run autonomous testing cycle
results = runner.auto_iterate(
    max_iterations=10,
    target_pass_rate=0.95,
    auto_improve=True  # AI agent can modify code to fix failures
)

print(f"Final pass rate: {results['pass_rate']}")
print(f"Iterations needed: {results['iterations']}")
print(f"Improvements applied: {results['improvements']}")
```

## Metrics & Reporting

### Tracked Metrics

1. **Tool Selection Accuracy** - % správně vybraných nástrojů
2. **Context Retention Rate** - % si AI pamatuje kontext
3. **Response Quality Score** - 0-1 score založený na relevanci
4. **Error Recovery Rate** - % úspěšně zotavených z chyb
5. **Prompt Adherence** - % dodržení původního požadavku

### Report Formats

- **Console output** - Real-time progress
- **JSON report** - Structured data pro parsing
- **HTML dashboard** - Vizualizace s grafy
- **Markdown summary** - Dokumentace výsledků

## Integration with CI/CD

```yaml
# .github/workflows/ai-testing.yml
name: AI Logic Testing

on: [push, pull_request]

jobs:
  test-ai-logic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: poetry install
      - name: Run AI E2E tests
        run: poetry run pytest tests/e2e/ -v --tb=short
      - name: Generate metrics report
        run: poetry run python tests/e2e/runner.py --report
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: ai-test-report
          path: tests/e2e/reports/
```

## Benefits for AI-Driven Development

1. **Autonomous Testing** - AI agent může testovat bez lidí
2. **Rapid Iteration** - Desítky testů za minuty místo hodin
3. **Consistent Validation** - Deterministické testy pro reprodukci
4. **Quality Metrics** - Objektivní měření AI performance
5. **Auto-Improvement** - AI může samostatně iterovat na zlepšení

## Next Steps

1. Expand fixtures and scenarios for provider fallback logic and thermal edge cases
2. Add scenario loader extensions (YAML, parameterized scenarios)
3. Integrate results into CI reports (artifacts and dashboards)

---

**Status:** Framework implementation complete (Phase 1-3), fixtures and runner integrated
**Target completion:** Done
**Expected benefit:** 10x faster AI logic iteration cycles
