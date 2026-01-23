import sqlite3
from unittest.mock import AsyncMock, MagicMock

import pytest

from mycoder.storage import StorageError, StorageManager


class FakeTime:
    def __init__(self, value: float = 0.0):
        self.value = value

    def __call__(self) -> float:
        return self.value


@pytest.mark.asyncio
async def test_save_and_get_history(tmp_path):
    fake_time = FakeTime()
    storage = StorageManager(tmp_path, time_provider=fake_time)

    message_id = await storage.save_interaction(
        "session-1", "user", "hello", metadata={"intent": "test"}
    )
    assert isinstance(message_id, int)

    history = await storage.get_history("session-1")
    assert history
    assert history[0]["content"] == "hello"
    assert history[0]["metadata"]["intent"] == "test"

    await storage.close()


@pytest.mark.asyncio
async def test_metadata_serialization_failure(tmp_path):
    storage = StorageManager(tmp_path)

    class Unserializable:
        pass

    await storage.save_interaction(
        "session-rare", "user", "hello", metadata={"payload": Unserializable()}
    )
    history = await storage.get_history("session-rare")
    assert history and history[0]["metadata"] == {}

    await storage.close()


@pytest.mark.asyncio
async def test_snapshot_and_rollback(tmp_path):
    storage = StorageManager(tmp_path)
    target = tmp_path / "doc.txt"
    target.write_text("initial")

    step_id = "step-rollback"
    await storage.create_snapshot(step_id, str(target))

    target.write_text("edited")
    restored = await storage.rollback(step_id)
    assert restored == [str(target)]
    assert target.read_text() == "initial"

    await storage.close()


@pytest.mark.asyncio
async def test_cleanup_old_sessions(tmp_path):
    fake_time = FakeTime(1000.0)
    storage = StorageManager(tmp_path, time_provider=fake_time)

    await storage.save_interaction("old", "user", "message")
    fake_time.value += 60 * 60 * 24 * 365
    await storage.cleanup_old_sessions(days=0)
    history = await storage.get_history("old")
    assert not history

    await storage.close()


@pytest.mark.asyncio
async def test_save_interaction_errors(monkeypatch, tmp_path):
    storage = StorageManager(tmp_path)

    # We need to mock aiosqlite.connect to fail or the connection's execute method to fail.
    # Since connect() is awaited, we need an AsyncMock.

    # Option 1: Mock connect to raise error
    mock_connect = AsyncMock(side_effect=sqlite3.Error("connection boom"))
    monkeypatch.setattr("mycoder.storage.aiosqlite.connect", mock_connect)

    with pytest.raises(StorageError):
        await storage.save_interaction("s", "user", "msg")

    # Option 2: Connection succeeds, but execute fails.
    # Reset storage for next check
    storage = StorageManager(tmp_path)

    mock_conn = MagicMock()
    mock_conn.execute = AsyncMock(side_effect=sqlite3.Error("execute boom"))
    mock_conn.commit = AsyncMock()
    # connect returns the connection object
    mock_connect_ok = AsyncMock(return_value=mock_conn)

    monkeypatch.setattr("mycoder.storage.aiosqlite.connect", mock_connect_ok)

    with pytest.raises(StorageError):
        await storage.save_interaction("s", "user", "msg")
