from mycoder.cli_interactive import InteractiveCLI


def test_plan_prompt_contains_task(monkeypatch):
    def _noop_init(self) -> None:
        """Avoid running the heavy InteractiveCLI init during testing."""
        return None

    monkeypatch.setattr(InteractiveCLI, "__init__", _noop_init)

    class DummyCLI(InteractiveCLI):
        pass

    cli = DummyCLI()
    cli.config_manager = None
    cli.mycoder = None
    prompt = cli._build_plan_prompt("Test task")

    assert "Test task" in prompt
