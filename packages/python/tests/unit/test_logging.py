"""
Tests for the package's logging behaviour.
"""

import json
import logging
import subprocess
import sys

from prompt_guard.logging import configure_logging, get_logger


def test_import_writes_nothing_and_adds_no_stream_handler():
    # Importing the package used to attach a JSON stream handler to the
    # "prompt_guard" logger and print a warning per missing optional extra.
    code = (
        "import logging, prompt_guard;"
        "handlers = logging.getLogger('prompt_guard').handlers;"
        "assert all(isinstance(h, logging.NullHandler) for h in handlers), handlers"
    )

    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""


def test_configured_logger_emits_each_record_once(capsys):
    root = logging.getLogger("prompt_guard")
    saved_handlers, saved_level = root.handlers[:], root.level
    try:
        configure_logging(level="INFO", json_format=True)
        logger = get_logger("test_component")

        logger.info("hello", component="unit")

        lines = [line for line in capsys.readouterr().err.splitlines() if line.strip()]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["message"] == "hello"
        assert record["context"] == {"component": "unit"}
    finally:
        root.handlers = saved_handlers
        root.setLevel(saved_level)
