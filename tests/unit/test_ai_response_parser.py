from mycoder.auto_executor import ActionType, AIResponseParser


def test_parse_file_create_code_block():
    parser = AIResponseParser()
    response = """```python\n# demo.py\nprint('hi')\n```"""
    actions = parser.parse(response)
    assert any(
        action.type == ActionType.CREATE_FILE and action.target == "demo.py"
        for action in actions
    )


def test_parse_commands_filters_dangerous():
    parser = AIResponseParser()
    response = """```bash\nls -la\nrm -rf /\n```"""
    actions = parser.parse(response)
    commands = [a.target for a in actions if a.type == ActionType.RUN_COMMAND]
    assert "ls -la" in commands
    assert not any("rm -rf" in cmd for cmd in commands)


def test_parse_installs():
    parser = AIResponseParser()
    response = "pip install requests"
    actions = parser.parse(response)
    assert any(
        action.type == ActionType.INSTALL_PACKAGE
        and action.target == "pip install requests"
        for action in actions
    )
