"""Enhanced file editing tool with unique string validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class EditResult:
    success: bool
    message: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None


class EditTool:
    """Edit tool with unique string validation."""

    def __init__(self, working_dir: Path) -> None:
        self.working_dir = working_dir
        self.read_files: set[str] = set()

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        path = Path(file_path)

        if str(path) not in self.read_files:
            return EditResult(
                success=False,
                message=f"File must be read before editing: {file_path}",
            )

        if not path.exists():
            return EditResult(
                success=False,
                message=f"File not found: {file_path}",
            )

        content = path.read_text(encoding="utf-8")
        count = content.count(old_string)
        if count == 0:
            return EditResult(
                success=False,
                message=f"String not found in file: {old_string[:50]}...",
            )

        if count > 1 and not replace_all:
            return EditResult(
                success=False,
                message=(
                    f"String is not unique ({count} occurrences). "
                    "Use replace_all=True or provide more context."
                ),
            )

        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        path.write_text(new_content, encoding="utf-8")
        return EditResult(
            success=True,
            message=f"Replaced {count if replace_all else 1} occurrence(s)",
            old_content=content,
            new_content=new_content,
        )

    def mark_as_read(self, file_path: str) -> None:
        self.read_files.add(file_path)

    def validate_edit(self, file_path: str, old_string: str) -> Tuple[bool, str]:
        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        content = path.read_text(encoding="utf-8")
        count = content.count(old_string)
        if count == 0:
            return False, "String not found"
        if count > 1:
            return False, f"String not unique ({count} occurrences)"

        return True, "Valid edit"
