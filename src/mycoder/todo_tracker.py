"""Todo tracker with simple JSON persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class TodoItem:
    """Single todo entry."""

    task: str
    status: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "TodoItem":
        return TodoItem(
            task=data.get("task", ""),
            status=data.get("status", "todo"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class TodoTracker:
    """Persist and manage todo items."""

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def list_items(self) -> List[TodoItem]:
        return self._load_items()

    def add(self, task: str) -> TodoItem:
        task = task.strip()
        if not task:
            raise ValueError("Task cannot be empty")
        now = datetime.now(timezone.utc).isoformat()
        item = TodoItem(task=task, status="todo", created_at=now, updated_at=now)
        items = self._load_items()
        items.append(item)
        self._save_items(items)
        return item

    def start(self, index: int) -> TodoItem:
        return self._set_status(index, "in_progress")

    def done(self, index: int) -> TodoItem:
        return self._set_status(index, "done")

    def clear_done(self) -> int:
        items = self._load_items()
        kept = [item for item in items if item.status != "done"]
        removed = len(items) - len(kept)
        if removed:
            self._save_items(kept)
        return removed

    def _set_status(self, index: int, status: str) -> TodoItem:
        items = self._load_items()
        if index < 1 or index > len(items):
            raise IndexError("Todo index out of range")
        item = items[index - 1]
        item.status = status
        item.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_items(items)
        return item

    def _load_items(self) -> List[TodoItem]:
        if not self.storage_path.exists():
            return []
        raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        return [TodoItem.from_dict(item) for item in raw]

    def _save_items(self, items: List[TodoItem]) -> None:
        payload = [item.to_dict() for item in items]
        temp_path = self.storage_path.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temp_path.replace(self.storage_path)
