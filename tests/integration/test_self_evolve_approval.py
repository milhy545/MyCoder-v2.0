from pathlib import Path

import pytest

from mycoder.self_evolve.manager import SelfEvolveManager
from mycoder.self_evolve.models import EvolveProposal


class DummyCoder:
    async def process_request(self, prompt: str, **kwargs):
        return {"content": "ok"}


@pytest.mark.asyncio
async def test_self_evolve_apply_requires_approval(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".git").mkdir()
    manager = SelfEvolveManager(DummyCoder(), tmp_path)

    proposal = EvolveProposal(
        proposal_id="test-proposal",
        status="proposed",
        summary="summary",
        rationale="",
        diff="diff --git a/foo b/foo",
        created_at=EvolveProposal.now_iso(),
        risk_score=0.0,
        risk_notes=[],
        applied_at=None,
        error=None,
        test_run=None,
    )
    manager.store.upsert(proposal)

    async def approve(_: EvolveProposal) -> bool:
        return False

    monkeypatch.setattr(manager, "_validate_diff", lambda diff: None)
    monkeypatch.setattr(manager, "_apply_patch", lambda diff: None)

    async def _run_tests():
        return manager._empty_test_run()

    monkeypatch.setattr(manager, "_run_tests", _run_tests)

    result = await manager.apply(
        proposal.proposal_id,
        require_approval=True,
        approval_callback=approve,
    )

    assert result.status == "rejected"
