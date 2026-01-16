"""
Scenario loading utilities for AI testing framework.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from tests.e2e.framework.scenario_engine import ScenarioDefinition, ScenarioType


def load_scenarios(scenario_type: Optional[str] = None) -> List[ScenarioDefinition]:
    """Load scenarios from JSON fixtures."""
    base_dir = Path(__file__).resolve().parents[1]
    prompts_path = base_dir / "fixtures" / "test_prompts.json"
    behaviors_path = base_dir / "fixtures" / "expected_behaviors.json"

    prompts_data = json.loads(prompts_path.read_text())
    behaviors_data = json.loads(behaviors_path.read_text())
    behaviors_map = {item["name"]: item for item in behaviors_data.get("scenarios", [])}

    if scenario_type:
        prompt_groups = {scenario_type: prompts_data.get(scenario_type, [])}
    else:
        prompt_groups = prompts_data

    scenarios: List[ScenarioDefinition] = []
    for group_name, group_items in prompt_groups.items():
        scenario_enum = _scenario_type_from_key(group_name)
        for item in group_items:
            behaviors = behaviors_map.get(item["name"], {})
            validation_rules = _build_validation_rules(behaviors)
            scenarios.append(
                ScenarioDefinition(
                    name=item["name"],
                    type=scenario_enum,
                    user_input=item["prompt"],
                    expected_tool=item["expected_tool"],
                    expected_confidence=item.get("confidence_min", 0.7),
                    context=item.get("context"),
                    validation_rules=validation_rules,
                    description=item.get("description", ""),
                )
            )

    return scenarios


def _scenario_type_from_key(key: str) -> ScenarioType:
    mapping = {
        "prompt_engineering": ScenarioType.PROMPT_ENGINEERING,
        "tool_selection": ScenarioType.TOOL_SELECTION,
        "context_awareness": ScenarioType.CONTEXT_AWARENESS,
        "error_handling": ScenarioType.ERROR_HANDLING,
        "multi_step": ScenarioType.MULTI_STEP,
    }
    return mapping.get(key, ScenarioType.TOOL_SELECTION)


def _build_validation_rules(
    behaviors: Dict[str, Any],
) -> List[Callable[[Dict[str, Any]], bool]]:
    rules: List[Callable[[Dict[str, Any]], bool]] = []

    expected_steps = behaviors.get("expected_steps")
    if expected_steps:
        rules.append(_rule_expected_steps(expected_steps))

    expected_actions = behaviors.get("expected_actions")
    if expected_actions:
        rules.append(_rule_expected_actions(expected_actions))

    expected_context_keys = behaviors.get("expected_context_keys")
    if expected_context_keys:
        rules.append(_rule_expected_context_keys(expected_context_keys))

    expected_alternatives = behaviors.get("expected_alternatives")
    if expected_alternatives:
        rules.append(_rule_expected_alternatives(expected_alternatives))

    return rules


def _rule_expected_steps(expected_steps: List[str]) -> Callable[[Dict[str, Any]], bool]:
    def _rule(response: Dict[str, Any]) -> bool:
        steps = response.get("steps", [])
        if len(steps) < len(expected_steps):
            return False
        for index, expected_tool in enumerate(expected_steps):
            if steps[index].get("tool") != expected_tool:
                return False
        return True

    return _rule


def _rule_expected_actions(
    expected_actions: List[str],
) -> Callable[[Dict[str, Any]], bool]:
    def _rule(response: Dict[str, Any]) -> bool:
        context_used = response.get("context_used", {})
        actions = context_used.get("recommended_actions", [])
        return all(action in actions for action in expected_actions)

    return _rule


def _rule_expected_context_keys(
    expected_context_keys: List[str],
) -> Callable[[Dict[str, Any]], bool]:
    def _rule(response: Dict[str, Any]) -> bool:
        context_used = response.get("context_used", {})
        return all(key in context_used for key in expected_context_keys)

    return _rule


def _rule_expected_alternatives(
    expected_alternatives: List[str],
) -> Callable[[Dict[str, Any]], bool]:
    def _rule(response: Dict[str, Any]) -> bool:
        alternatives = response.get("alternatives", [])
        return all(item in alternatives for item in expected_alternatives)

    return _rule
