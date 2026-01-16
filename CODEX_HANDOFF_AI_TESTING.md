# Codex Handoff: AI Testing Framework Implementation

## Summary

Claude Code připravil kompletní task pro implementaci **AI Testing Framework** - self-testing suite pro iterativní vývoj AI logiky, promptů a tool selection v MyCoder v2.1.1.

## Files Created for You

### 1. Main Task Document
**File:** `CODEX_TASK_AI_TESTING_FRAMEWORK.md`
- ✅ Kompletní task s 3 fázemi
- ✅ TODO checklist
- ✅ Code templates (~2000+ řádků)
- ✅ Testing strategy
- ✅ Success criteria

### 2. Framework Design
**File:** `tests/e2e/AI_TESTING_FRAMEWORK.md`
- ✅ Architecture overview
- ✅ Component descriptions
- ✅ Usage examples
- ✅ Integration guide

### 3. Implementation Plan
**File:** `tests/e2e/IMPLEMENTATION_PLAN.md`
- ✅ 3-day roadmap
- ✅ Prioritized tasks
- ✅ POC guide (2h)
- ✅ Quality gates

### 4. Quick Start
**File:** `tests/e2e/QUICK_START.md`
- ✅ Step-by-step guide
- ✅ Usage examples
- ✅ Troubleshooting
- ✅ CI/CD integration

## What You Need to Do

### Phase 1: POC (2 hours) - PRIORITY

**Goal:** Minimal working prototype

**Files to create:**
1. `tests/e2e/framework/ai_simulator.py` (~400 lines)
   - Class: `SimpleAISimulator` - pattern-based tool selection
   - Class: `AISimulator` - advanced with intelligence levels

2. `tests/e2e/framework/scenario_engine.py` (~250 lines)
   - Class: `TestScenario` - scenario definition
   - Class: `ScenarioEngine` - scenario execution

3. `tests/e2e/test_poc_tool_selection.py` (~300 lines)
   - Test class: `TestSimpleAISimulatorPOC`
   - 15+ test methods

**Verify POC:**
```bash
poetry run pytest tests/e2e/test_poc_tool_selection.py -v
# Expected: 15+ tests PASSED in < 5 seconds
```

### Phase 2: Full Framework (Day 2)

**Files to create:**
1. `tests/e2e/framework/assertion_framework.py` (~200 lines)
2. `tests/e2e/framework/metrics_collector.py` (~180 lines)
3. `tests/e2e/test_ai_prompt_engineering.py` (~400 lines)
4. `tests/e2e/test_ai_tool_selection.py` (~350 lines)
5. `tests/e2e/test_ai_context_retention.py` (~300 lines)
6. `tests/e2e/test_ai_error_handling.py` (~250 lines)
7. `tests/e2e/fixtures/*.json` (3 files)

**Target:** 50+ scenarios, pass rate > 90%

### Phase 3: Automation (Day 3)

**Files to create:**
1. `tests/e2e/runner.py` (~400 lines) - self-test runner with auto-iteration
2. `tests/e2e/framework/report_generator.py` (~250 lines)
3. `tests/e2e/README.md` - documentation
4. `tests/e2e/examples/*.py` - usage examples

**Target:** Full autonomous testing cycle working

## Key Concepts

### AI Simulator
Mock AI responses bez real API calls. Uses pattern matching:
```python
"Read config.json" → {"tool": "file_read", "confidence": 0.9}
"Run tests" → {"tool": "bash", "confidence": 0.85}
"Update and test" → {"tool": "multi_step", "steps": [...]}
```

### Scenario Engine
Execute test scenarios and validate results:
```python
scenario = TestScenario(
    name="file_read",
    user_input="Read config.json",
    expected_tool="file_read",
    expected_confidence=0.8
)
result = engine.execute_scenario(scenario)
assert result.passed
```

### Auto-Iteration
Autonomous testing loop:
```
Run tests → Analyze failures → Generate improvements → Apply fixes → Re-run
```

## Templates Provided

All code templates jsou v `CODEX_TASK_AI_TESTING_FRAMEWORK.md`:
- ✅ Complete class implementations
- ✅ Method signatures with docstrings
- ✅ Example usage
- ✅ TODO comments for extensions

## Testing Instructions

### After Each Phase

```bash
# Format code
poetry run black tests/e2e/
poetry run isort tests/e2e/

# Lint
poetry run flake8 tests/e2e/

# Test
poetry run pytest tests/e2e/ -v
```

### Expected Results

**Phase 1 (POC):**
- 15+ tests passing
- Execution time < 5 seconds
- Simple tool selection working

**Phase 2 (Full):**
- 50+ tests passing
- Tool accuracy > 95%
- Context retention > 90%

**Phase 3 (Auto):**
- Auto-iteration working
- Reports generating
- Pass rate > 95%

## Reference Code

### Existing E2E Test (Pattern to Follow)
`tests/e2e/test_simulation.py` - Mock server setup, fixtures, scenarios

### Existing Unit Tests (Style Guide)
`tests/unit/test_command_parser.py` - Test structure, assertions, coverage

### Existing Integration Tests (Complex Scenarios)
`tests/integration/test_enhanced_mycoder_integration.py` - Multi-component testing

## Success Criteria

### Phase 1 Done When:
- [ ] AI Simulator works (pattern matching correct)
- [ ] Scenario Engine executes tests
- [ ] 15+ POC tests passing
- [ ] Takes < 2 hours to implement

### Phase 2 Done When:
- [ ] Assertion framework complete
- [ ] Metrics collector tracking all metrics
- [ ] 50+ scenarios implemented
- [ ] Pass rate > 90%

### Phase 3 Done When:
- [ ] Self-test runner functional
- [ ] Auto-iteration mode working
- [ ] Reports generating (console, JSON, HTML)
- [ ] CI/CD ready

## Common Pitfalls to Avoid

1. **Don't overthink POC** - Simple pattern matching is enough
2. **Test determinism** - Same input must give same output
3. **Performance** - Full suite should run < 5 minutes
4. **Documentation** - Docstrings on all public methods
5. **Edge cases** - Handle empty/invalid inputs gracefully

## Questions?

All answers are in the task files:
- **Architecture?** → `tests/e2e/AI_TESTING_FRAMEWORK.md`
- **Implementation order?** → `tests/e2e/IMPLEMENTATION_PLAN.md`
- **Quick start?** → `tests/e2e/QUICK_START.md`
- **Detailed tasks?** → `CODEX_TASK_AI_TESTING_FRAMEWORK.md`

## Final Notes

### Time Estimate
- Phase 1 (POC): 2 hours
- Phase 2 (Full): 1 day
- Phase 3 (Auto): 1 day
- **Total: 2-3 days**

### Lines of Code
- Framework core: ~1,700 lines
- Test scenarios: ~1,800 lines
- Documentation: ~500 lines
- **Total: ~4,000 lines**

### Value Proposition
**Before:** Testing AI logic takes hours of manual work per iteration
**After:** Autonomous testing completes 50+ scenarios in 5 minutes
**ROI:** 10x faster iteration cycles for AI development

## Start Command

```bash
cd /home/milhy777/Develop/MyCoder-v2.0

# Read task
cat CODEX_TASK_AI_TESTING_FRAMEWORK.md

# Create structure
mkdir -p tests/e2e/framework tests/e2e/scenarios tests/e2e/fixtures

# Start with Phase 1
# Implement: tests/e2e/framework/ai_simulator.py
# Then: tests/e2e/framework/scenario_engine.py
# Then: tests/e2e/test_poc_tool_selection.py

# Verify POC
poetry run pytest tests/e2e/test_poc_tool_selection.py -v
```

---

**Good luck! When Phase 1 done, report back s výsledky testů.** 🚀

---

**Prepared by:** Claude Code (Claude Sonnet 4.5)
**Date:** 2026-01-14
**Project:** MyCoder v2.1.1 - AI Testing Framework
