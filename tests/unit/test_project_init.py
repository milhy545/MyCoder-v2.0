import json

from mycoder.project_init import generate_project_guide


def test_generate_project_guide_includes_detected_info(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndescription = "Demo app"\n',
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        json.dumps(
            {"name": "demo-js", "scripts": {"test": "pytest", "lint": "eslint ."}}
        ),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n\nShort summary.\n", encoding="utf-8")
    (tmp_path / "src").mkdir()

    content = generate_project_guide(tmp_path)

    assert "Name: demo" in content
    assert "Description: Demo app" in content
    assert "- src/" in content
    assert "`npm install`" in content
    assert "`npm run test`" in content
    assert "`poetry install`" in content
