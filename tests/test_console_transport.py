"""Tests for ConsoleTransport."""

import json
from io import StringIO
from unittest.mock import patch

from msw_logger.transports.console import ConsoleTransport
from msw_logger.types import StructuredLog


def _make_log(level: str = "INFO", **overrides) -> StructuredLog:
    log: StructuredLog = {
        "timestamp": "2025-01-15T10:30:00.000Z",
        "level": level,
        "category": "TEST",
        "operation": "test-operation",
        "message": "Test message",
        "environment": "server",
    }
    log.update(overrides)
    return log


class TestConsoleMethodMapping:
    """Mirrors TS ConsoleTransport.test.ts."""

    def test_trace_uses_stdout(self):
        transport = ConsoleTransport()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("TRACE"))
        assert "TRACE" in mock_out.getvalue()

    def test_debug_uses_stdout(self):
        transport = ConsoleTransport()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("DEBUG"))
        assert "DEBUG" in mock_out.getvalue()

    def test_info_uses_stdout(self):
        transport = ConsoleTransport()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("INFO"))
        assert "INFO" in mock_out.getvalue()

    def test_warn_uses_stderr(self):
        transport = ConsoleTransport()
        with patch("sys.stderr", new_callable=StringIO) as mock_err:
            transport.log(_make_log("WARN"))
        assert "WARN" in mock_err.getvalue()

    def test_error_uses_stderr(self):
        transport = ConsoleTransport()
        with patch("sys.stderr", new_callable=StringIO) as mock_err:
            transport.log(_make_log("ERROR"))
        assert "ERROR" in mock_err.getvalue()


class TestLogOutputContent:
    def test_includes_level(self):
        transport = ConsoleTransport()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("INFO"))
        assert "INFO" in mock_out.getvalue()

    def test_includes_category(self):
        transport = ConsoleTransport()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("INFO"))
        assert "TEST" in mock_out.getvalue()

    def test_includes_message(self):
        transport = ConsoleTransport()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("INFO"))
        assert "Test message" in mock_out.getvalue()

    def test_includes_operation(self):
        transport = ConsoleTransport()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("INFO"))
        assert "test-operation" in mock_out.getvalue()

    def test_includes_data(self):
        transport = ConsoleTransport()
        log = _make_log("INFO", data={"key": "value"})
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(log)
        output = mock_out.getvalue()
        assert "Data:" in output
        assert "key" in output

    def test_includes_request_id(self):
        transport = ConsoleTransport()
        log = _make_log("INFO", request_id="req-abc-123")
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(log)
        assert "req-abc-123" in mock_out.getvalue()

    def test_includes_error_details(self):
        transport = ConsoleTransport()
        log = _make_log(
            "ERROR",
            error={"name": "ValueError", "message": "bad value", "stack": "traceback..."},
        )
        with patch("sys.stderr", new_callable=StringIO) as mock_err:
            transport.log(log)
        output = mock_err.getvalue()
        assert "ValueError" in output
        assert "bad value" in output


class TestJsonFormat:
    def test_json_outputs_valid_json(self):
        transport = ConsoleTransport(format="json")
        log = _make_log("INFO")
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(log)
        output = mock_out.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"

    def test_json_is_single_line(self):
        transport = ConsoleTransport(format="json")
        log = _make_log("INFO", data={"key": "value"})
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(log)
        output = mock_out.getvalue()
        # Should be exactly one line (content + newline from print)
        assert output.count("\n") == 1

    def test_json_includes_all_fields(self):
        transport = ConsoleTransport(format="json")
        log = _make_log("INFO", request_id="req-123", data={"key": "value"})
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(log)
        parsed = json.loads(mock_out.getvalue())
        assert parsed["timestamp"] == "2025-01-15T10:30:00.000Z"
        assert parsed["level"] == "INFO"
        assert parsed["category"] == "TEST"
        assert parsed["operation"] == "test-operation"
        assert parsed["message"] == "Test message"
        assert parsed["environment"] == "server"
        assert parsed["request_id"] == "req-123"
        assert parsed["data"] == {"key": "value"}

    def test_json_routes_all_levels_to_stdout(self):
        """JSON mode always uses stdout (for log collectors), even for WARN/ERROR."""
        for level in ("TRACE", "DEBUG", "INFO", "WARN", "ERROR"):
            transport = ConsoleTransport(format="json")
            with patch("sys.stdout", new_callable=StringIO) as mock_out, \
                 patch("sys.stderr", new_callable=StringIO) as mock_err:
                transport.log(_make_log(level))
            assert mock_out.getvalue(), f"{level} should write to stdout"
            assert not mock_err.getvalue(), f"{level} should NOT write to stderr"

    def test_pretty_format_unchanged(self):
        """Explicit pretty format behaves like default."""
        transport = ConsoleTransport(format="pretty")
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("INFO"))
        output = mock_out.getvalue()
        assert "Message:" in output  # Pretty format has labels
