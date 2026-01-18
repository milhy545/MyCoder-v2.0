"""Data models for Self-Evolve MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


@dataclass
class TestCommandResult:
    """Result of a single test command."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
        }


@dataclass
class TestRunSummary:
    """Aggregated results for a test run."""

    started_at: str
    duration_ms: int
    results: List[TestCommandResult] = field(default_factory=list)

    def failures(self) -> List[TestCommandResult]:
        return [result for result in self.results if result.exit_code != 0]

    def to_dict(self) -> Dict[str, object]:
        return {
            "started_at": self.started_at,
            "duration_ms": self.duration_ms,
            "results": [result.to_dict() for result in self.results],
        }


@dataclass
class EvolveSignal:
    """Signals collected for self-evolution proposals."""

    summary: str
    failure_output: str
    test_run: TestRunSummary

    def to_dict(self) -> Dict[str, object]:
        return {
            "summary": self.summary,
            "failure_output": self.failure_output,
            "test_run": self.test_run.to_dict(),
        }


@dataclass
class EvolveProposal:
    """Proposed self-evolve change."""

    proposal_id: str
    status: str
    summary: str
    rationale: str
    diff: str
    created_at: str
    risk_score: float = 0.0
    risk_notes: List[str] = field(default_factory=list)
    applied_at: Optional[str] = None
    error: Optional[str] = None
    test_run: Optional[TestRunSummary] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "status": self.status,
            "summary": self.summary,
            "rationale": self.rationale,
            "diff": self.diff,
            "created_at": self.created_at,
            "risk_score": self.risk_score,
            "risk_notes": self.risk_notes,
            "applied_at": self.applied_at,
            "error": self.error,
            "test_run": self.test_run.to_dict() if self.test_run else None,
        }

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class ErrorType(Enum):
    """Error classification for TTL rules."""

    HARD = "HARD"
    SOFT = "SOFT"


class EvolutionStatus(Enum):
    """Status of recorded failure resolution."""

    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"


class AdvisoryResult(Enum):
    """Result of the FailureMemory advisory check."""

    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass
class FailureRecord:
    """Represents a stored failure event."""

    id: int
    tool_signature: str
    env_snapshot_hash: str
    error_type: ErrorType
    retry_count: int
    created_at: str
    updated_at: str
    error_message: Optional[str]
    tool_name: str
    evolution_status: EvolutionStatus

    def is_expired(self) -> bool:
        """Check TTL expiration."""
        from datetime import timedelta

        updated = datetime.fromisoformat(self.updated_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        ttl = (
            timedelta(days=7)
            if self.error_type == ErrorType.HARD
            else timedelta(hours=1)
        )

        return (now - updated) > ttl

    @staticmethod
    def from_row(row: tuple) -> "FailureRecord":
        return FailureRecord(
            id=row[0],
            tool_signature=row[1],
            env_snapshot_hash=row[2],
            error_type=ErrorType(row[3]),
            retry_count=row[4],
            created_at=row[5],
            updated_at=row[6],
            error_message=row[7],
            tool_name=row[8],
            evolution_status=EvolutionStatus(row[9]),
        )


@dataclass
class Advisory:
    """Advisory response from FailureMemory."""

    result: AdvisoryResult
    reason: str
    failure_record: Optional[FailureRecord] = None
    retry_count: int = 0
