"""Unit tests for FailureMemory (reflexion mechanism)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mycoder.self_evolve.failure_memory import (
    AdvisoryResult,
    ErrorType,
    FailureMemory,
)


@pytest.fixture
def failure_memory(tmp_path: Path) -> FailureMemory:
    return FailureMemory(db_path=tmp_path / "failure_memory.db")


def test_compute_tool_signature_is_deterministic(failure_memory: FailureMemory):
    sig1 = failure_memory._compute_tool_signature("file_read", {"path": "a.py"})
    sig2 = failure_memory._compute_tool_signature("file_read", {"path": "a.py"})
    assert sig1 == sig2


def test_compute_env_snapshot_hash_returns_32_chars(tmp_path: Path):
    env_hash = FailureMemory.compute_env_snapshot_hash(working_directory=tmp_path)
    assert isinstance(env_hash, str)
    assert len(env_hash) == 32


def test_classify_error_soft_vs_hard(failure_memory: FailureMemory):
    assert failure_memory._classify_error("Connection refused") == ErrorType.SOFT
    assert failure_memory._classify_error("SyntaxError: invalid") == ErrorType.HARD


def test_record_failure_creates_record(failure_memory: FailureMemory):
    env_hash = FailureMemory.compute_env_snapshot_hash(working_directory=Path.cwd())
    failure_memory.record_failure(
        tool_name="file_read",
        params={"path": "test.py"},
        error_message="File not found",
        env_snapshot_hash=env_hash,
    )
    stats = failure_memory.get_stats()
    assert stats["total"] == 1


def test_record_failure_increments_retry_count(failure_memory: FailureMemory):
    env_hash = FailureMemory.compute_env_snapshot_hash(working_directory=Path.cwd())
    for _ in range(2):
        failure_memory.record_failure(
            tool_name="file_read",
            params={"path": "test.py"},
            error_message="File not found",
            env_snapshot_hash=env_hash,
        )

    records = failure_memory.get_recent_failures()
    assert records[0].retry_count == 2


def test_check_advisory_allows_first_time(failure_memory: FailureMemory):
    advisory = failure_memory.check_advisory(
        "file_read", {"path": "test.py"}, env_snapshot_hash="env1"
    )
    assert advisory.result == AdvisoryResult.ALLOW


def test_check_advisory_warns_after_threshold(failure_memory: FailureMemory):
    env_hash = "env_warn"
    failure_memory.record_failure(
        tool_name="file_read",
        params={"path": "test.py"},
        error_message="File not found",
        env_snapshot_hash=env_hash,
    )

    advisory = failure_memory.check_advisory(
        "file_read", {"path": "test.py"}, env_snapshot_hash=env_hash
    )
    assert advisory.result == AdvisoryResult.WARN


def test_check_advisory_blocks_after_threshold(failure_memory: FailureMemory):
    env_hash = "env_block"
    for _ in range(3):
        failure_memory.record_failure(
            tool_name="file_read",
            params={"path": "test.py"},
            error_message="File not found",
            env_snapshot_hash=env_hash,
        )

    advisory = failure_memory.check_advisory(
        "file_read", {"path": "test.py"}, env_snapshot_hash=env_hash
    )
    assert advisory.result == AdvisoryResult.BLOCK


def test_check_advisory_allows_different_env(failure_memory: FailureMemory):
    env1 = "env_alpha"
    env2 = "env_beta"
    for _ in range(3):
        failure_memory.record_failure(
            tool_name="file_read",
            params={"path": "test.py"},
            error_message="File not found",
            env_snapshot_hash=env1,
        )

    advisory = failure_memory.check_advisory(
        "file_read", {"path": "test.py"}, env_snapshot_hash=env2
    )
    assert advisory.result == AdvisoryResult.ALLOW


def test_clear_failure_marks_resolved(failure_memory: FailureMemory):
    env_hash = FailureMemory.compute_env_snapshot_hash(working_directory=Path.cwd())

    failure_memory.record_failure(
        tool_name="file_read",
        params={"path": "test.py"},
        error_message="File not found",
        env_snapshot_hash=env_hash,
    )

    success = failure_memory.clear_failure(
        tool_name="file_read",
        params={"path": "test.py"},
        env_snapshot_hash=env_hash,
    )
    assert success

    advisory = failure_memory.check_advisory(
        "file_read", {"path": "test.py"}, env_snapshot_hash=env_hash
    )
    assert advisory.result == AdvisoryResult.ALLOW


def test_ttl_expiration_hard_errors(failure_memory: FailureMemory):
    env_hash = "hard_env"
    failure_memory.record_failure(
        tool_name="file_read",
        params={"path": "ttl.py"},
        error_message="SyntaxError: boo",
        env_snapshot_hash=env_hash,
    )

    now = datetime.now(timezone.utc)
    expired_time = (
        now - timedelta(days=FailureMemory.HARD_ERROR_TTL_DAYS + 1)
    ).isoformat()

    with failure_memory._get_connection() as conn:
        conn.execute(
            "UPDATE failure_records SET updated_at = ? WHERE env_snapshot_hash = ?",
            (expired_time, env_hash),
        )
        conn.commit()

    deleted = failure_memory._cleanup_expired()
    assert deleted == 1


def test_ttl_expiration_soft_errors(failure_memory: FailureMemory):
    env_hash = "soft_env"
    failure_memory.record_failure(
        tool_name="file_read",
        params={"path": "ttl_soft.py"},
        error_message="Connection timeout",
        env_snapshot_hash=env_hash,
    )

    now = datetime.now(timezone.utc)
    expired_time = (
        now - timedelta(hours=FailureMemory.SOFT_ERROR_TTL_HOURS + 1)
    ).isoformat()

    with failure_memory._get_connection() as conn:
        conn.execute(
            "UPDATE failure_records SET updated_at = ? WHERE env_snapshot_hash = ?",
            (expired_time, env_hash),
        )
        conn.commit()

    deleted = failure_memory._cleanup_expired()
    assert deleted == 1
