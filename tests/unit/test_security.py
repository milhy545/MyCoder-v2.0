import pytest

from mycoder.security import FileSecurityManager, SecurityError


def test_validate_path_allows_working_directory(tmp_path):
    manager = FileSecurityManager(tmp_path, allow_tmp=False)
    allowed_file = tmp_path / "notes.txt"
    allowed_file.write_text("hello")

    resolved = manager.validate_path(allowed_file)
    assert resolved == allowed_file.resolve()


def test_validate_path_rejects_outside_directory(tmp_path):
    manager = FileSecurityManager(tmp_path, allow_tmp=False)
    outside = tmp_path.parent / "other.txt"

    with pytest.raises(SecurityError):
        manager.validate_path(outside)


def test_extra_allowed_paths_accepts_custom(tmp_path):
    manager = FileSecurityManager(tmp_path, allow_tmp=False)
    extra = tmp_path / "extra"
    extra.mkdir()
    target = extra / "file.txt"
    target.write_text("data")

    result = manager.validate_path(target, extra_allowed_paths=[extra])
    assert result == target.resolve()
