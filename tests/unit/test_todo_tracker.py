from pathlib import Path

import pytest

from mycoder.todo_tracker import TodoTracker


def test_add_and_list_items(tmp_path: Path) -> None:
    tracker = TodoTracker(tmp_path / "todo.json")

    item = tracker.add("Test task")
    items = tracker.list_items()

    assert item.task == "Test task"
    assert len(items) == 1
    assert items[0].status == "todo"


def test_start_and_done(tmp_path: Path) -> None:
    tracker = TodoTracker(tmp_path / "todo.json")
    tracker.add("Task A")

    started = tracker.start(1)
    assert started.status == "in_progress"

    done = tracker.done(1)
    assert done.status == "done"


def test_clear_done(tmp_path: Path) -> None:
    tracker = TodoTracker(tmp_path / "todo.json")
    tracker.add("Task A")
    tracker.add("Task B")
    tracker.done(1)

    removed = tracker.clear_done()
    items = tracker.list_items()

    assert removed == 1
    assert len(items) == 1
    assert items[0].task == "Task B"


def test_empty_task_raises(tmp_path: Path) -> None:
    tracker = TodoTracker(tmp_path / "todo.json")

    with pytest.raises(ValueError):
        tracker.add("   ")
