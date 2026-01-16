from mycoder.cli_interactive import InteractiveCLI


def test_plan_prompt_contains_task(monkeypatch):
    class DummyCLI(InteractiveCLI):
        def __init__(self) -> None:
            pass

    cli = DummyCLI()
    prompt = cli._build_plan_prompt("Test task")

    assert "Test task" in prompt
