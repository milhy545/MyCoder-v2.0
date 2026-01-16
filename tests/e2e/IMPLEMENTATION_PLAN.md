# AI Testing Framework - Implementation Plan

## Prioritizovaný Implementační Plán

### Fáze 1: Foundation (Day 1)

**Priorita: CRITICAL** - Základní infrastruktura

#### 1.1 AI Simulator
```
File: tests/e2e/framework/ai_simulator.py
Lines: ~300
Status: NEW

Features:
- Mock AI response generation
- Pattern-based response selection
- Tool usage simulation
- Deterministic behavior for testing
```

#### 1.2 Scenario Engine
```
File: tests/e2e/framework/scenario_engine.py
Lines: ~250
Status: NEW

Features:
- Scenario definition schema
- Scenario execution engine
- Context injection
- Result capture
```

### Fáze 2: Validation & Metrics (Day 1-2)

**Priorita: HIGH** - Validation framework

#### 2.1 Assertion Framework
```
File: tests/e2e/framework/assertion_framework.py
Lines: ~200
Status: NEW

Features:
- AI-specific assertions (tool_selected, context_retained, etc.)
- Custom assertion messages
- Failure diagnostics
```

#### 2.2 Metrics Collector
```
File: tests/e2e/framework/metrics_collector.py
Lines: ~180
Status: NEW

Features:
- Metric tracking (accuracy, quality, performance)
- Aggregation & statistics
- Trend analysis
```

### Fáze 3: Test Scenarios (Day 2)

**Priorita: HIGH** - Actual test cases

#### 3.1 Prompt Engineering Tests
```
File: tests/e2e/test_ai_prompt_engineering.py
Lines: ~400
Status: NEW

Test Cases:
- Simple commands (read file, run command)
- Complex multi-step tasks
- Ambiguous requests
- Context-dependent prompts
```

#### 3.2 Tool Selection Tests
```
File: tests/e2e/test_ai_tool_selection.py
Lines: ~350
Status: NEW

Test Cases:
- Correct tool selection
- Tool preference logic
- Fallback behavior
- Thermal-aware selection
```

#### 3.3 Context Awareness Tests
```
File: tests/e2e/test_ai_context_retention.py
Lines: ~300
Status: NEW

Test Cases:
- Multi-turn conversations
- File context retention
- Variable/state tracking
- Long-term memory
```

### Fáze 4: Automation (Day 3)

**Priorita: MEDIUM** - Self-improvement loop

#### 4.1 Self-Test Runner
```
File: tests/e2e/runner.py
Lines: ~400
Status: NEW

Features:
- Autonomous test execution
- Auto-iteration on failures
- Improvement suggestion
- Report generation
```

#### 4.2 Report Generator
```
File: tests/e2e/framework/report_generator.py
Lines: ~250
Status: NEW

Features:
- Console output
- JSON reports
- HTML dashboard
- Markdown summaries
```

## Quick Start Implementation

### Immediate Next Steps (30 min)

1. **Create directory structure:**
```bash
mkdir -p tests/e2e/framework
mkdir -p tests/e2e/scenarios
mkdir -p tests/e2e/fixtures
touch tests/e2e/framework/__init__.py
touch tests/e2e/scenarios/__init__.py
```

2. **Implement minimal AI Simulator (MVP):**
```python
# tests/e2e/framework/ai_simulator.py
class SimpleAISimulator:
    """Minimal AI simulator for immediate testing"""

    def simulate(self, prompt, context=None):
        # Pattern matching for common scenarios
        if "read" in prompt.lower() and "file" in prompt.lower():
            return {"tool": "file_read", "confidence": 0.9}
        elif "run" in prompt.lower() or "execute" in prompt.lower():
            return {"tool": "bash", "confidence": 0.85}
        # ... more patterns
        return {"tool": "ask_user", "confidence": 0.5}
```

3. **Create first test scenario:**
```python
# tests/e2e/test_simple_commands.py
def test_file_read_command():
    simulator = SimpleAISimulator()
    result = simulator.simulate("Read mycoder_config.json")

    assert result["tool"] == "file_read"
    assert result["confidence"] > 0.8
```

### Proof of Concept (2 hours)

**Goal:** Demonstrovat funkčnost základního frameworku

```python
# tests/e2e/test_poc_tool_selection.py
"""Proof of Concept - Tool Selection Testing"""

import pytest
from tests.e2e.framework.ai_simulator import SimpleAISimulator

class TestToolSelectionPOC:
    """POC: Validate tool selection logic works"""

    def setup_method(self):
        self.simulator = SimpleAISimulator()

    def test_file_operations(self):
        """Test file operation tool selection"""
        scenarios = [
            ("Read config.json", "file_read"),
            ("Write to output.txt", "file_write"),
            ("List files in src/", "file_list"),
        ]

        for prompt, expected_tool in scenarios:
            result = self.simulator.simulate(prompt)
            assert result["tool"] == expected_tool, \
                f"Failed for '{prompt}': expected {expected_tool}, got {result['tool']}"

    def test_command_execution(self):
        """Test bash command tool selection"""
        scenarios = [
            ("Run tests", "bash"),
            ("Execute poetry install", "bash"),
            ("Check git status", "bash"),
        ]

        for prompt, expected_tool in scenarios:
            result = self.simulator.simulate(prompt)
            assert result["tool"] == expected_tool

    def test_ambiguous_requests(self):
        """Test handling of ambiguous requests"""
        result = self.simulator.simulate("Fix the bug")

        # Should either ask for clarification or analyze context
        assert result["tool"] in ["ask_user", "analyze_context"]
        assert result["confidence"] < 0.7  # Low confidence expected

    def test_multi_step_planning(self):
        """Test multi-step task planning"""
        result = self.simulator.simulate(
            "Update dependencies and run tests",
            context={"working_dir": "/project"}
        )

        # Should break into multiple tools
        assert "steps" in result
        assert len(result["steps"]) >= 2
        assert any("poetry update" in str(step) for step in result["steps"])
        assert any("pytest" in str(step) for step in result["steps"])
```

### Run POC

```bash
# Create minimal simulator
cat > tests/e2e/framework/ai_simulator.py << 'EOF'
class SimpleAISimulator:
    def simulate(self, prompt, context=None):
        prompt_lower = prompt.lower()

        # File operations
        if "read" in prompt_lower and "file" in prompt_lower:
            return {"tool": "file_read", "confidence": 0.9}
        if "write" in prompt_lower and "file" in prompt_lower:
            return {"tool": "file_write", "confidence": 0.9}
        if "list" in prompt_lower and "file" in prompt_lower:
            return {"tool": "file_list", "confidence": 0.85}

        # Command execution
        if any(word in prompt_lower for word in ["run", "execute", "check"]):
            return {"tool": "bash", "confidence": 0.85}

        # Multi-step tasks
        if "and" in prompt_lower or "then" in prompt_lower:
            steps = prompt.split(" and ")
            return {
                "tool": "multi_step",
                "steps": [self.simulate(step) for step in steps],
                "confidence": 0.8
            }

        # Ambiguous - ask for clarification
        return {"tool": "ask_user", "confidence": 0.5}
EOF

# Run POC test
poetry run pytest tests/e2e/test_poc_tool_selection.py -v
```

## Development Workflow

### For AI Agent (Claude Code)

**Autonomous Testing Loop:**

```python
# Pseudo-code for AI agent workflow

while pass_rate < 0.95 and iterations < max_iterations:
    # 1. Run tests
    results = run_all_scenarios()

    # 2. Analyze failures
    failures = [r for r in results if not r.passed]

    # 3. Generate improvements
    for failure in failures:
        improvement = analyze_failure(failure)

        # 4. Apply fix
        apply_improvement(improvement)

    # 5. Verify fix
    new_result = run_scenario(failure.scenario)

    # 6. Update metrics
    update_metrics(new_result)

    iterations += 1

# Generate final report
generate_report(all_results)
```

### Example Session

```bash
# Terminal session example
$ poetry run python tests/e2e/runner.py --auto-iterate

🚀 AI Testing Framework - Auto-Iteration Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Iteration 1/10
  Running 45 scenarios...
  ✅ 38 passed, ❌ 7 failed
  Pass rate: 84.4%

🔍 Analyzing failures...
  Failure 1: Tool selection - Expected 'file_read', got 'bash'
    → Issue: Prompt pattern too broad
    → Fix: Add file extension detection
  Failure 2: Context retention - Lost context after 3 turns
    → Issue: Context window not preserved
    → Fix: Implement context summarization

🔧 Applying improvements...
  ✓ Updated prompt patterns in ai_simulator.py
  ✓ Added context preservation logic

📊 Iteration 2/10
  Running 45 scenarios...
  ✅ 42 passed, ❌ 3 failed
  Pass rate: 93.3%

  ... continues until pass_rate > 95% ...

✅ Target achieved after 4 iterations!
  Final pass rate: 95.6%
  Total improvements: 12

📄 Report generated: tests/e2e/reports/run_2026-01-14_20-45.html
```

## Integration Points

### With Existing MyCoder Code

```python
# Enhanced MyCoder integration
class EnhancedMyCoderV2:

    async def _select_tool_for_task(self, task, context):
        """Tool selection with E2E test validation"""

        # Normal selection logic
        selected_tool = await self.tool_orchestrator.select_tool(task)

        # In test mode, validate selection
        if self.test_mode:
            expected = self.test_scenario.expected_tool
            if selected_tool != expected:
                self.test_failures.append({
                    "task": task,
                    "expected": expected,
                    "actual": selected_tool,
                    "context": context
                })

        return selected_tool
```

## Success Criteria

### Definition of Done

- [ ] AI Simulator generates realistic responses
- [ ] 50+ test scenarios covering key use cases
- [ ] Assertion framework validates AI behavior
- [ ] Self-test runner executes autonomously
- [ ] Reports show actionable insights
- [ ] Pass rate > 95% on core scenarios
- [ ] CI/CD integration working
- [ ] Documentation complete

### Quality Gates

1. **Tool Selection Accuracy:** > 95%
2. **Context Retention Rate:** > 90%
3. **Error Recovery Rate:** > 85%
4. **Test Execution Time:** < 5 minutes for full suite
5. **False Positive Rate:** < 5%

## Timeline Estimate

- **Day 1 Morning:** Foundation (ai_simulator, scenario_engine)
- **Day 1 Afternoon:** Validation (assertions, metrics)
- **Day 2 Morning:** Test scenarios (prompts, tools, context)
- **Day 2 Afternoon:** Integration testing
- **Day 3 Morning:** Automation (runner, auto-iteration)
- **Day 3 Afternoon:** Reports, documentation, polish

**Total:** 3 days for complete framework + 50+ scenarios

## Next Immediate Action

**What to do RIGHT NOW:**

```bash
# 1. Create structure
cd /home/milhy777/Develop/MyCoder-v2.0
mkdir -p tests/e2e/framework tests/e2e/scenarios tests/e2e/fixtures

# 2. Create __init__.py files
touch tests/e2e/framework/__init__.py
touch tests/e2e/scenarios/__init__.py

# 3. Start with minimal AI simulator
# (Claude Code can implement this in next message)

# 4. Write first POC test
# (Claude Code can write test_poc_tool_selection.py)

# 5. Verify POC works
poetry run pytest tests/e2e/test_poc_tool_selection.py -v
```

**Ready to implement? Řekni "implement POC" a začnu s minimálním funkčním prototypem!**
