"""Sandbox helpers for self-evolve dry-run execution."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class WorktreeSandbox:
    """Manage temporary git worktrees for dry-run validation."""

    def __init__(self, repo_root: Path, base_dir: Optional[Path] = None) -> None:
        self.repo_root = repo_root
        self.base_dir = base_dir

    def create(self) -> Path:
        base_dir = (
            self.base_dir or self.repo_root / ".mycoder" / "self_evolve" / "worktrees"
        )
        base_dir.mkdir(parents=True, exist_ok=True)
        worktree_path = Path(tempfile.mkdtemp(prefix="self-evolve-", dir=base_dir))
        add_result = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree_path)],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
        if add_result.returncode != 0:
            shutil.rmtree(worktree_path, ignore_errors=True)
            raise RuntimeError(add_result.stderr.strip() or "Failed to create worktree")
        return worktree_path

    def cleanup(self, worktree_path: Path) -> None:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
        shutil.rmtree(worktree_path, ignore_errors=True)
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
