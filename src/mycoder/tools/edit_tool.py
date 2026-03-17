"""Enhanced file editing tool with unique string validation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


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

        # Normalize to absolute path for consistency
        if not path.is_absolute():
            path = self.working_dir / path
        path = path.resolve()

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

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            return EditResult(
                success=False,
                message=f"Failed to read file: {e}",
            )

        old_content = content

        occurrences = content.count(old_string)
        if occurrences == 0:
            return EditResult(
                success=False,
                message=(
                    f"String not found in {file_path}. "
                    "Ensure exact matching including whitespace/indentation."
                ),
                old_content=old_content,
            )

        if occurrences > 1 and not replace_all:
            return EditResult(
                success=False,
                message=(
                    f"Found {occurrences} occurrences of the string in {file_path}. "
                    "Add more context to make it unique, or set replace_all=True."
                ),
                old_content=old_content,
            )

        new_content = content.replace(old_string, new_string)

        try:
            path.write_text(new_content, encoding="utf-8")
        except OSError as e:
            return EditResult(
                success=False,
                message=f"Failed to write file: {e}",
                old_content=old_content,
            )

        logger.info("Successfully edited: %s", file_path)
        return EditResult(
            success=True,
            message=f"Successfully edited {file_path}",
            old_content=old_content,
            new_content=new_content,
        )

    def mark_read(self, file_path: str) -> None:
        """Mark a file as read so it can be edited."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.working_dir / path
        self.read_files.add(str(path.resolve()))

    def get_unique_strings(self, content: str) -> Tuple[str, ...]:
        """Return lines that appear exactly once in content."""
        lines = content.splitlines()
        return tuple(line for line in lines if lines.count(line) == 1)
