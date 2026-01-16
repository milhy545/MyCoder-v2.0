"""Tool selection scenarios."""

from __future__ import annotations

from typing import List

from tests.e2e.framework.scenario_engine import ScenarioDefinition
from tests.e2e.scenarios.fixture_loader import load_scenarios


def get_scenarios() -> List[ScenarioDefinition]:
    return load_scenarios("tool_selection")
