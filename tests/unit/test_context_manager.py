import json

import pytest


class FakeTime:
    def __init__(self, start: float = 0.0):
        self.value = start

    def __call__(self) -> float:
        return self.value


def test_cache_returns_cached_context_until_ttl(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    config_file = project / "mycoder_config.json"
    config_file.write_text(json.dumps({"debug_mode": True}))

    fake_time = FakeTime()
    manager = ContextManager(project, cache_ttl_seconds=2, time_provider=fake_time)

    first_context = manager.get_context()
    assert first_context.config["debug_mode"] is True

    config_file.write_text(json.dumps({"debug_mode": False}))
    fake_time.value += 1
    second_context = manager.get_context()
    assert second_context.config["debug_mode"] is True

    fake_time.value += 2.5
    third_context = manager.get_context()
    assert third_context.config["debug_mode"] is False


def test_force_reload_ignores_cache(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    config_file = project / "mycoder_config.json"
    config_file.write_text(json.dumps({"debug_mode": True}))

    manager = ContextManager(project, cache_ttl_seconds=60)
    first = manager.get_context()
    config_file.write_text(json.dumps({"debug_mode": False}))
    second = manager.get_context(force_reload=True)
    assert second.config["debug_mode"] is False
