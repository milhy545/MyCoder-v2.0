from pathlib import Path

from mycoder.tools.edit_tool import EditTool


def test_edit_requires_read_mark(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello world", encoding="utf-8")
    tool = EditTool(tmp_path)

    result = tool.edit(str(file_path), "hello", "hi")

    assert result.success is False
    assert "must be read" in result.message


def test_edit_replaces_unique_string(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("alpha beta", encoding="utf-8")
    tool = EditTool(tmp_path)
    tool.mark_as_read(str(file_path))

    result = tool.edit(str(file_path), "beta", "gamma")

    assert result.success is True
    assert "Replaced" in result.message
    assert file_path.read_text(encoding="utf-8") == "alpha gamma"


def test_edit_requires_unique_string_without_replace_all(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("dup dup", encoding="utf-8")
    tool = EditTool(tmp_path)
    tool.mark_as_read(str(file_path))

    result = tool.edit(str(file_path), "dup", "new")

    assert result.success is False
    assert "not unique" in result.message


def test_edit_replace_all_allows_multiple(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("dup dup", encoding="utf-8")
    tool = EditTool(tmp_path)
    tool.mark_as_read(str(file_path))

    result = tool.edit(str(file_path), "dup", "new", replace_all=True)

    assert result.success is True
    assert file_path.read_text(encoding="utf-8") == "new new"


def test_validate_edit_reports_status(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("alpha beta alpha", encoding="utf-8")
    tool = EditTool(tmp_path)

    valid, message = tool.validate_edit(str(file_path), "beta")
    assert valid is True
    assert message == "Valid edit"

    valid, message = tool.validate_edit(str(file_path), "alpha")
    assert valid is False
    assert "not unique" in message

    valid, message = tool.validate_edit(str(file_path), "missing")
    assert valid is False
    assert message == "String not found"
