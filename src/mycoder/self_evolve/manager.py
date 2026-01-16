"""Self-evolve manager orchestrating proposal and apply flows."""

from __future__ import annotations

import json
import random
import string
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .models import EvolveProposal
from .proposal_engine import ProposalEngine
from .risk_assessor import RiskAssessor
from .sandbox import WorktreeSandbox
from .signal_collector import SignalCollector
from .storage import ProposalStore
from .test_runner import TestRunner


class SelfEvolveManager:
    """Coordinate self-evolve proposals and application."""

    def __init__(self, coder, working_directory: Path) -> None:
        self.coder = coder
        self.repo_root = self._find_repo_root(working_directory)
        self.config = self._load_config()
        self.store = ProposalStore(self._storage_dir())
        self.signal_collector = SignalCollector(
            max_output_chars=self.config["max_output_chars"]
        )
        self.test_runner = TestRunner(
            self.repo_root, timeout_seconds=self.config["test_timeout_seconds"]
        )
        self.proposal_engine = ProposalEngine(
            coder,
            self.repo_root,
            allowed_paths=self.config["allowed_paths"],
        )
        self.risk_assessor = RiskAssessor()

    async def propose(self) -> Optional[EvolveProposal]:
        self._prune_proposals()
        test_run = await self._run_tests()
        signal = self.signal_collector.build_signal(test_run)
        if not signal.test_run.failures():
            return None

        draft = await self.proposal_engine.generate(signal)
        if draft.error:
            proposal = self._build_proposal(
                summary="Proposal failed",
                rationale="",
                diff="",
                status="failed",
                error=draft.error,
                test_run=test_run,
            )
            self.store.upsert(proposal)
            return proposal

        validation_error = self._validate_diff(draft.diff)
        if validation_error:
            proposal = self._build_proposal(
                summary=draft.summary or "Proposal invalid",
                rationale=draft.rationale,
                diff=draft.diff,
                status="failed",
                error=validation_error,
                test_run=test_run,
            )
            self.store.upsert(proposal)
            return proposal

        risk = self.risk_assessor.assess(draft.diff)
        proposal = self._build_proposal(
            summary=draft.summary,
            rationale=draft.rationale,
            diff=draft.diff,
            status="proposed",
            error=None,
            test_run=test_run,
            risk_score=risk.score,
            risk_notes=risk.notes,
        )
        self.store.upsert(proposal)
        self.store.store_patch(proposal.proposal_id, draft.diff)
        return proposal

    async def propose_from_issue(self, issue: str) -> EvolveProposal:
        issue = issue.strip()
        if not issue:
            raise ValueError("Issue description is required")
        self._prune_proposals()
        test_run = await self._run_tests() if self.config["run_tests_on_issue"] else None
        if test_run is None:
            test_run = self._empty_test_run()
        signal = self.signal_collector.build_signal(test_run)
        signal.summary = f"User reported issue: {issue}"
        signal.failure_output = signal.failure_output or "No failing test output provided."

        draft = await self.proposal_engine.generate(signal)
        if draft.error:
            proposal = self._build_proposal(
                summary="Proposal failed",
                rationale="",
                diff="",
                status="failed",
                error=draft.error,
                test_run=test_run,
            )
            self.store.upsert(proposal)
            return proposal

        validation_error = self._validate_diff(draft.diff)
        if validation_error:
            proposal = self._build_proposal(
                summary=draft.summary or "Proposal invalid",
                rationale=draft.rationale,
                diff=draft.diff,
                status="failed",
                error=validation_error,
                test_run=test_run,
            )
            self.store.upsert(proposal)
            return proposal

        risk = self.risk_assessor.assess(draft.diff)
        proposal = self._build_proposal(
            summary=draft.summary,
            rationale=draft.rationale,
            diff=draft.diff,
            status="proposed",
            error=None,
            test_run=test_run,
            risk_score=risk.score,
            risk_notes=risk.notes,
        )
        self.store.upsert(proposal)
        self.store.store_patch(proposal.proposal_id, draft.diff)
        return proposal

    async def apply(
        self,
        proposal_id: str,
        require_approval: bool = True,
        approval_callback: Optional[Callable[[EvolveProposal], Awaitable[bool]]] = None,
    ) -> EvolveProposal:
        proposal = self.store.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")
        if proposal.status != "proposed":
            raise ValueError(f"Proposal not in proposed state: {proposal.status}")

        if require_approval:
            approved = await self._request_user_approval(
                proposal, approval_callback
            )
            if not approved:
                proposal.status = "rejected"
                proposal.error = "User rejected proposal"
                self.store.upsert(proposal)
                return proposal

        validation_error = self._validate_diff(proposal.diff)
        if validation_error:
            proposal.status = "failed"
            proposal.error = validation_error
            self.store.upsert(proposal)
            return proposal

        apply_error = self._apply_patch(proposal.diff)
        if apply_error:
            proposal.status = "failed"
            proposal.error = apply_error
            self.store.upsert(proposal)
            return proposal

        test_run = await self._run_tests()
        proposal.test_run = test_run
        proposal.applied_at = EvolveProposal.now_iso()
        if not test_run.failures():
            proposal.status = "applied"
            self.store.upsert(proposal)
            return proposal

        if self.config["auto_rollback_on_failure"]:
            rollback_error = self._rollback_patch(proposal.diff)
            if rollback_error:
                proposal.status = "applied_with_failures"
                proposal.error = rollback_error
            else:
                proposal.status = "rolled_back"
        else:
            proposal.status = "applied_with_failures"
        self.store.upsert(proposal)
        return proposal

    async def dry_run(self, proposal_id: str) -> Dict[str, Any]:
        proposal = self.store.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        validation_error = self._validate_diff(proposal.diff)
        if validation_error:
            return {"success": False, "error": validation_error}

        sandbox = WorktreeSandbox(self.repo_root)
        worktree_path = sandbox.create()
        try:
            apply_error = self._apply_patch_in_dir(proposal.diff, worktree_path)
            if apply_error:
                return {"success": False, "error": apply_error}

            test_runner = TestRunner(
                worktree_path, timeout_seconds=self.config["test_timeout_seconds"]
            )
            test_run = await self._run_in_thread(
                test_runner.run_commands,
                list(self.config["test_commands"]),
            )
            return {
                "success": not test_run.failures(),
                "test_results": test_run.to_dict(),
                "affected_files": self._extract_paths(proposal.diff),
            }
        finally:
            sandbox.cleanup(worktree_path)

    def list_proposals(self) -> List[EvolveProposal]:
        return self.store.load_all()

    def show_patch(self, proposal_id: str) -> Optional[str]:
        proposal = self.store.get(proposal_id)
        if not proposal:
            return None
        return proposal.diff

    def _storage_dir(self) -> Path:
        return self.repo_root / ".mycoder" / "self_evolve"

    def _load_config(self) -> Dict[str, object]:
        config_path = self.repo_root / ".mycoder" / "self_evolve" / "config.json"
        defaults = {
            "allowed_paths": ["src/", "tests/", "docs/", "README.md", "pyproject.toml"],
            "test_commands": [
                "poetry run pytest tests/unit/ -v",
                "poetry run pytest tests/e2e/ -v",
            ],
            "max_output_chars": 8000,
            "max_patch_bytes": 200000,
            "test_timeout_seconds": 900,
            "run_tests_on_issue": True,
            "auto_rollback_on_failure": True,
            "max_proposals": 100,
            "auto_cleanup_days": 30,
        }
        if not config_path.exists():
            return defaults
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return {**defaults, **data}
        except Exception:
            return defaults

    def _build_proposal(
        self,
        summary: str,
        rationale: str,
        diff: str,
        status: str,
        error: Optional[str],
        test_run,
        risk_score: float = 0.0,
        risk_notes: Optional[List[str]] = None,
    ) -> EvolveProposal:
        proposal_id = self._generate_id()
        return EvolveProposal(
            proposal_id=proposal_id,
            status=status,
            summary=summary or "Self-evolve proposal",
            rationale=rationale or "",
            diff=diff,
            created_at=EvolveProposal.now_iso(),
            risk_score=risk_score,
            risk_notes=risk_notes or [],
            applied_at=None,
            error=error,
            test_run=test_run,
        )

    def _generate_id(self) -> str:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{EvolveProposal.now_iso().replace(':', '').replace('-', '')}-{suffix}"

    def _validate_diff(self, diff: str) -> Optional[str]:
        if not diff.strip():
            return "Empty diff"
        if len(diff.encode("utf-8")) > int(self.config["max_patch_bytes"]):
            return "Diff exceeds maximum allowed size"

        allowed = self.config["allowed_paths"]
        touched = self._extract_paths(diff)
        for path in touched:
            if not self._is_path_allowed(path, allowed):
                return f"Diff touches disallowed path: {path}"
        return None

    def _extract_paths(self, diff: str) -> List[str]:
        paths = []
        for line in diff.splitlines():
            if line.startswith("diff --git "):
                parts = line.split()
                if len(parts) >= 4:
                    path = parts[2].replace("a/", "", 1)
                    paths.append(path)
        return paths

    def _is_path_allowed(self, path: str, allowed_paths: List[str]) -> bool:
        normalized = path.lstrip("/")
        for allowed in allowed_paths:
            if allowed.endswith("/"):
                if normalized.startswith(allowed):
                    return True
            else:
                if normalized == allowed:
                    return True
        return False

    def _apply_patch(self, diff: str) -> Optional[str]:
        return self._apply_patch_in_dir(diff, self.repo_root)

    def _apply_patch_in_dir(self, diff: str, working_directory: Path) -> Optional[str]:
        check = subprocess.run(
            ["git", "apply", "--check", "-"],
            cwd=working_directory,
            input=diff,
            text=True,
            capture_output=True,
        )
        if check.returncode != 0:
            return check.stderr.strip() or "Patch validation failed"

        apply_result = subprocess.run(
            ["git", "apply", "-"],
            cwd=working_directory,
            input=diff,
            text=True,
            capture_output=True,
        )
        if apply_result.returncode != 0:
            return apply_result.stderr.strip() or "Patch apply failed"
        return None

    def _rollback_patch(self, diff: str) -> Optional[str]:
        rollback = subprocess.run(
            ["git", "apply", "-R", "-"],
            cwd=self.repo_root,
            input=diff,
            text=True,
            capture_output=True,
        )
        if rollback.returncode != 0:
            return rollback.stderr.strip() or "Patch rollback failed"
        return None

    async def _run_tests(self):
        return await self._run_in_thread(
            self.test_runner.run_commands,
            list(self.config["test_commands"]),
        )

    async def _run_in_thread(self, func, *args):
        import asyncio

        return await asyncio.to_thread(func, *args)

    def _find_repo_root(self, working_directory: Path) -> Path:
        current = working_directory
        for _ in range(5):
            if (current / ".git").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        return working_directory

    def _empty_test_run(self):
        from .models import TestRunSummary

        return TestRunSummary(
            started_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=0,
            results=[],
        )

    async def _request_user_approval(
        self,
        proposal: EvolveProposal,
        approval_callback: Optional[Callable[[EvolveProposal], Awaitable[bool]]],
    ) -> bool:
        if not approval_callback:
            return False
        try:
            return await approval_callback(proposal)
        except Exception:
            return False

    def _prune_proposals(self) -> None:
        self._cleanup_old_proposals()
        self._enforce_max_proposals()

    def _cleanup_old_proposals(self) -> int:
        proposals = self.store.load_all()
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=int(self.config["auto_cleanup_days"])
        )
        to_keep = []
        removed = 0
        for proposal in proposals:
            try:
                created = datetime.fromisoformat(proposal.created_at)
            except ValueError:
                created = datetime.now(timezone.utc)
            if created > cutoff or proposal.status == "applied":
                to_keep.append(proposal)
                continue
            removed += 1
            patch_file = self.store.patch_dir / f"{proposal.proposal_id}.patch"
            patch_file.unlink(missing_ok=True)
        if removed:
            self.store.save_all(to_keep)
        return removed

    def _enforce_max_proposals(self) -> int:
        proposals = self.store.load_all()
        max_proposals = int(self.config["max_proposals"])
        if max_proposals <= 0 or len(proposals) <= max_proposals:
            return 0

        def _created_at(proposal: EvolveProposal) -> datetime:
            try:
                return datetime.fromisoformat(proposal.created_at)
            except ValueError:
                return datetime.now(timezone.utc)

        sorted_proposals = sorted(proposals, key=_created_at)
        removable = [
            proposal for proposal in sorted_proposals if proposal.status != "applied"
        ]
        keep = list(proposals)
        removed = 0
        while len(keep) > max_proposals and (removable or keep):
            candidate = removable.pop(0) if removable else keep[0]
            keep = [proposal for proposal in keep if proposal != candidate]
            patch_file = self.store.patch_dir / f"{candidate.proposal_id}.patch"
            patch_file.unlink(missing_ok=True)
            removed += 1

        if removed:
            self.store.save_all(keep)
        return removed
