import pytest

from mycoder.auto_executor import ActionType, AutoExecutor


@pytest.mark.asyncio
async def test_auto_executor_executes_confirmed_actions():
    response = """```python\n# demo.py\nprint('hi')\n```\n```bash\nls -la\n```"""
    auto_executor = AutoExecutor(require_confirmation=True)
    confirmed = []
    executed = []

    async def confirm(action):
        confirmed.append(action.type)
        return True

    async def execute(action):
        executed.append(action.target)
        return True

    results = await auto_executor.process_response(
        response, confirm_callback=confirm, execute_callback=execute
    )

    assert all(success for _, success in results)
    assert ActionType.CREATE_FILE in confirmed
    assert "demo.py" in "".join(executed)
    assert "ls -la" in executed


@pytest.mark.asyncio
async def test_auto_executor_skip_confirmation_when_disabled():
    response = """```bash\necho test\n```"""
    auto_executor = AutoExecutor(require_confirmation=False)
    executed = []

    async def execute(action):
        executed.append(action.target)
        return True

    results = await auto_executor.process_response(
        response, confirm_callback=None, execute_callback=execute
    )

    assert results
    assert executed == ["echo test"]
