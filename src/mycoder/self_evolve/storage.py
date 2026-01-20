"""Storage helpers for self-evolve proposals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from filelock import FileLock

from .models import EvolveProposal, TestCommandResult, TestRunSummary


class ProposalStore:
    """Persist proposals to disk for review and application."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.proposals_file = self.base_dir / "proposals.json"
        self.lock_file = self.base_dir / "proposals.lock"
        self.lock = FileLock(self.lock_file, timeout=10)
        self.patch_dir = self.base_dir / "patches"
        self.patch_dir.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> List[EvolveProposal]:
        with self.lock:
            return self._load_all_unsafe()

    def _load_all_unsafe(self) -> List[EvolveProposal]:
        if not self.proposals_file.exists():
            return []
        raw = json.loads(self.proposals_file.read_text(encoding="utf-8"))
        proposals = []
        for item in raw:
            test_run = None
            test_run_raw = item.get("test_run")
            if test_run_raw:
                test_run = TestRunSummary(
                    started_at=test_run_raw.get("started_at", ""),
                    duration_ms=test_run_raw.get("duration_ms", 0),
                    results=[
                        TestCommandResult(
                            command=result.get("command", ""),
                            exit_code=result.get("exit_code", 0),
                            stdout=result.get("stdout", ""),
                            stderr=result.get("stderr", ""),
                            duration_ms=result.get("duration_ms", 0),
                        )
                        for result in test_run_raw.get("results", [])
                    ],
                )
            proposals.append(
                EvolveProposal(
                    proposal_id=item["proposal_id"],
                    status=item["status"],
                    summary=item["summary"],
                    rationale=item.get("rationale", ""),
                    diff=item.get("diff", ""),
                    created_at=item["created_at"],
                    risk_score=item.get("risk_score", 0.0),
                    risk_notes=item.get("risk_notes", []) or [],
                    applied_at=item.get("applied_at"),
                    error=item.get("error"),
                    test_run=test_run,
                )
            )
        return proposals

    def save_all(self, proposals: List[EvolveProposal]) -> None:
        with self.lock:
            self._save_all_unsafe(proposals)

    def _save_all_unsafe(self, proposals: List[EvolveProposal]) -> None:
        payload = [proposal.to_dict() for proposal in proposals]
        temp_file = self.proposals_file.with_suffix(".tmp")
        temp_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temp_file.replace(self.proposals_file)

    def get(self, proposal_id: str) -> Optional[EvolveProposal]:
        with self.lock:
            for proposal in self._load_all_unsafe():
                if proposal.proposal_id == proposal_id:
                    return proposal
        return None

    def upsert(self, proposal: EvolveProposal) -> None:
        with self.lock:
            proposals = self._load_all_unsafe()
            updated = False
            for index, existing in enumerate(proposals):
                if existing.proposal_id == proposal.proposal_id:
                    proposals[index] = proposal
                    updated = True
                    break
            if not updated:
                proposals.append(proposal)
            self._save_all_unsafe(proposals)

    def store_patch(self, proposal_id: str, diff: str) -> Path:
        path = self.patch_dir / f"{proposal_id}.patch"
        path.write_text(diff, encoding="utf-8")
        return path
