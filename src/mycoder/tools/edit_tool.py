import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EditResult:
    success: bool
    message: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None


class EditTool:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()

    def execute(self, file_path: str, old_text: str, new_text: str) -> str:
        target_path = (self.workspace_root / file_path).resolve()

        if not str(target_path).startswith(str(self.workspace_root)):
            return f"ERROR: Security violation. Path outside workspace ({target_path})"

        if not target_path.exists():
            return f"ERROR: File {file_path} does not exist."

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()

            occurrences = content.count(old_text)
            if occurrences == 0:
                return "ERROR: old_text not found. Ensure exact matching including whitespace/indentation."
            elif occurrences > 1:
                return f"ERROR: old_text found {occurrences} times. Add more context to old_text to make it unique."

            new_content = content.replace(old_text, new_text)

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            logger.info(f"Successfully edited: {file_path}")
            return f"SUCCESS: File {file_path} successfully updated."

        except Exception as e:
            logger.error(f"Error editing {file_path}: {e}")
            return f"ERROR: Unexpected write error: {str(e)}"
