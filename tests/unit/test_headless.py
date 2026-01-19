import io
import json
import logging
import sys

from mycoder.headless import JsonlHandler


def test_jsonl_handler_emits_jsonl(monkeypatch):
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

    stream = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stream)

    handler.emit(log_record)
    output = stream.getvalue().strip()
    assert output
    payload = json.loads(output)
    assert payload["message"] == "hello jsonl"
    assert payload["logger"] == "test"
