"""Tests for ConsoleTransport."""

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
