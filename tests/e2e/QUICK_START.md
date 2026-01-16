# AI Testing Framework - Quick Start Guide

## For Codex: How to Implement

### Step 1: Read Task File (5 min)

```bash
# Přečti si kompletní task
cat CODEX_TASK_AI_TESTING_FRAMEWORK.md

# Prostuduj reference dokumenty
cat tests/e2e/AI_TESTING_FRAMEWORK.md
cat tests/e2e/IMPLEMENTATION_PLAN.md
```

### Step 2: Create Directory Structure (1 min)

```bash
cd /home/milhy777/Develop/MyCoder-v2.0

mkdir -p tests/e2e/framework
mkdir -p tests/e2e/scenarios
mkdir -p tests/e2e/fixtures
mkdir -p tests/e2e/reports
mkdir -p tests/e2e/examples

touch tests/e2e/framework/__init__.py
touch tests/e2e/scenarios/__init__.py
```

### Step 3: Implement POC (Fáze 1) - 2 hours

**Priority Order:**

1. **AI Simulator** (40 min)
   ```bash
   # Create: tests/e2e/framework/ai_simulator.py
   # ~400 lines
   # Implement: SimpleAISimulator, AISimulator, IntelligenceLevel
   ```

2. **Scenario Engine** (30 min)
   ```bash
   # Create: tests/e2e/framework/scenario_engine.py
   # ~250 lines
   # Implement: TestScenario, ScenarioResult, ScenarioEngine
   ```

3. **POC Tests** (40 min)
   ```bash
   # Create: tests/e2e/test_poc_tool_selection.py
   # ~300 lines
   # Implement: TestSimpleAISimulatorPOC, TestAdvancedAISimulatorPOC
   ```

4. **Verify POC** (10 min)
   ```bash
   poetry run pytest tests/e2e/test_poc_tool_selection.py -v
   # Expected: 15+ tests passing
   ```

### Step 4: Full Framework (Fáze 2) - Day 2

1. **Assertion Framework** (~200 lines)
2. **Metrics Collector** (~180 lines)
3. **Comprehensive Test Scenarios** (~1200 lines total)
4. **Fixture Library** (JSON files)

### Step 5: Automation (Fáze 3) - Day 3

1. **Self-Test Runner** (~400 lines)
2. **Report Generator** (~250 lines)
3. **Integration & Documentation**

## For Human: How to Use After Implementation

### Run POC Tests

```bash
# Quick smoke test
poetry run pytest tests/e2e/test_poc_tool_selection.py -v

# Expected output:
# ✅ 15+ tests passed
# ⏱️  < 5 seconds
```

### Run Full Test Suite

```bash
# All E2E tests
poetry run pytest tests/e2e/ -v

# Specific test type
poetry run pytest tests/e2e/test_ai_tool_selection.py -v
```

### Auto-Iteration Mode (AI Self-Testing)

```bash
# Run with auto-iteration
poetry run python tests/e2e/runner.py --auto-iterate --max-iterations 10

# Output:
# 📊 Iteration 1/10: 84.4% passed
# 🔧 Applying 7 improvements...
# 📊 Iteration 2/10: 93.3% passed
# ...
# ✅ Target achieved after 4 iterations!
```

### Generate Reports

```bash
# Console report
poetry run python tests/e2e/runner.py --report

# HTML dashboard
poetry run python tests/e2e/runner.py --report --format html

# JSON export
poetry run python tests/e2e/runner.py --report --format json --output results.json
```

## Common Use Cases

### Use Case 1: Test Prompt Changes

```python
# After modifying prompts in your code
poetry run pytest tests/e2e/test_ai_prompt_engineering.py -v

# Check metrics
poetry run python tests/e2e/runner.py --scenario-type prompt_engineering --report
```

### Use Case 2: Validate Tool Selection Logic

```python
# After changing tool selection logic
poetry run pytest tests/e2e/test_ai_tool_selection.py -v

# Check accuracy
# Expected: Tool Accuracy > 95%
```

### Use Case 3: AI Agent Self-Improvement Loop

```python
# In Python script
from tests.e2e.runner import SelfTestRunner

runner = SelfTestRunner()
results = runner.auto_iterate(
    max_iterations=10,
    target_pass_rate=0.95,
    auto_improve=True  # Let AI fix failures
)

print(f"Final pass rate: {results['pass_rate']}")
print(f"Improvements applied: {len(results['improvements'])}")
```

## Troubleshooting

### Issue: Tests failing with import errors

```bash
# Make sure you're in project root
cd /home/milhy777/Develop/MyCoder-v2.0

# Install dependencies
poetry install

# Check Python path
poetry run python -c "import sys; print(sys.path)"
```

### Issue: POC tests not passing

```bash
# Run with verbose output
poetry run pytest tests/e2e/test_poc_tool_selection.py -vv -s

# Check AI simulator patterns
poetry run python -c "from tests.e2e.framework.ai_simulator import SimpleAISimulator; s = SimpleAISimulator(); print(s.simulate('Read file.txt'))"
```

### Issue: Auto-iteration not improving

```bash
# Check improvement suggestions
poetry run python tests/e2e/runner.py --analyze-only

# Manual review of failures
poetry run pytest tests/e2e/ -v --tb=short | grep FAILED
```

## Performance Targets

- **POC Tests:** < 5 seconds for 15+ tests
- **Full Suite:** < 5 minutes for 50+ scenarios
- **Auto-Iteration:** < 10 minutes for 10 iterations
- **Report Generation:** < 2 seconds

## Quality Gates

- ✅ Tool Selection Accuracy: > 95%
- ✅ Context Retention Rate: > 90%
- ✅ Error Recovery Rate: > 85%
- ✅ Pass Rate: > 95% on core scenarios
- ✅ Test Coverage: > 85% of framework code

## Integration with CI/CD

```yaml
# .github/workflows/ai-testing.yml
name: AI Testing

on: [push, pull_request]

jobs:
  ai-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: poetry install
      - run: poetry run pytest tests/e2e/ -v --tb=short
      - run: poetry run python tests/e2e/runner.py --report --format json
      - uses: actions/upload-artifact@v3
        with:
          name: ai-test-results
          path: tests/e2e/reports/
```

## Next Steps After Implementation

1. **Run Full Suite:** `poetry run pytest tests/e2e/ -v`
2. **Verify Metrics:** Check pass rate > 95%
3. **Test Auto-Iteration:** `poetry run python tests/e2e/runner.py --auto-iterate`
4. **Generate Report:** Review HTML dashboard
5. **Document Results:** Update AGENTS.md with implementation notes

## Success Indicators

✅ Framework implemented
✅ POC tests passing (15+)
✅ Full suite passing (50+)
✅ Auto-iteration working
✅ Reports generating
✅ CI/CD integrated
✅ Documentation complete

**When all indicators green → Framework ready for production use!** 🎉
