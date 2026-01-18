from mycoder.cli_interactive import InteractiveCLI


def test_plan_prompt_contains_task(monkeypatch):
    class DummyCLI(InteractiveCLI):
        def __init__(self) -> None:
            # Minimal init - only set required attributes for testing
            self.config_manager = None
            self.mycoder = None

    cli = DummyCLI()
    prompt = cli._build_plan_prompt("Test task")

    assert "Test task" in prompt
