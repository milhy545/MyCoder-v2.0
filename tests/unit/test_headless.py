import io
import json
import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mycoder.headless import JsonlHandler, main


def test_jsonl_handler_default_stream():
    """Test that JsonlHandler defaults to stderr."""
    with patch("sys.stderr", new=io.StringIO()) as mock_stderr:
        handler = JsonlHandler()
        log_record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="hello jsonl",
            args=(),
            exc_info=None,
        )

        handler.emit(log_record)
        output = mock_stderr.getvalue().strip()
        assert output
        payload = json.loads(output)
        assert payload["message"] == "hello jsonl"
        assert payload["logger"] == "test"


def test_jsonl_handler_custom_stream():
    """Test that JsonlHandler uses the provided stream."""
    stream = io.StringIO()
    handler = JsonlHandler(stream=stream)
    log_record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="custom stream",
        args=(),
        exc_info=None,
    )

    handler.emit(log_record)
    output = stream.getvalue().strip()
    assert output
    payload = json.loads(output)
    assert payload["message"] == "custom stream"


@pytest.mark.asyncio
async def test_main_output_to_file(tmp_path, monkeypatch):
    """Test that main correctly writes output to a file."""
    output_file = tmp_path / "result.json"

    # Mock arguments
    test_args = [
        "headless.py",
        "test prompt",
        "--output",
        str(output_file),
        "--auto-approve",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    with (
        patch("mycoder.headless.EnhancedMyCoderV2") as mock_coder_cls,
        patch("mycoder.headless.ContextManager") as mock_ctx_mgr_cls,
        patch("sys.exit") as mock_exit,
    ):

        mock_coder_instance = mock_coder_cls.return_value
        # Make initialize a coroutine
        mock_coder_instance.initialize = AsyncMock()
        mock_coder_instance.process_request = AsyncMock(
            return_value={
                "success": True,
                "content": "Test response",
                "metadata": {"model": "test-model"},
            }
        )

        mock_ctx_mgr_instance = mock_ctx_mgr_cls.return_value
        mock_ctx_mgr_instance.get_context.return_value = MagicMock(config={})

        await main()

        # Verify result file
        assert output_file.exists()
        result_data = json.loads(output_file.read_text())
        assert result_data["success"] is True
        assert result_data["content"] == "Test response"
        mock_exit.assert_called_with(0)


@pytest.mark.asyncio
async def test_main_log_to_file(tmp_path, monkeypatch):
    """Test that main correctly writes logs to a file."""
    log_file = tmp_path / "test.log"

    # Mock arguments
    test_args = [
        "headless.py",
        "test prompt",
        "--log-file",
        str(log_file),
        "--auto-approve",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    with (
        patch("mycoder.headless.EnhancedMyCoderV2") as mock_coder_cls,
        patch("mycoder.headless.ContextManager") as mock_ctx_mgr_cls,
        patch("sys.exit") as mock_exit,
    ):

        mock_coder_instance = mock_coder_cls.return_value
        mock_coder_instance.initialize = AsyncMock()
        mock_coder_instance.process_request = AsyncMock(return_value={"success": True})

        mock_ctx_mgr_instance = mock_ctx_mgr_cls.return_value
        mock_ctx_mgr_instance.get_context.return_value = MagicMock(config={})

        await main()

        # Verify log file
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Initializing Headless Agent" in log_content
        mock_exit.assert_called_with(0)
