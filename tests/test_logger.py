"""Tests for Logger class."""

from msw_logger.logger import Logger
from msw_logger.types import LogLevel, LoggerConfig, StructuredLog


class MockTransport:
    """Mock transport that captures logs."""

    def __init__(self):
        self.name = "mock"
        self.logs: list[StructuredLog] = []

    def log(self, entry: StructuredLog) -> None:
        self.logs.append(entry)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


def _make_logger(level: LogLevel = LogLevel.INFO, **kwargs) -> tuple[Logger, MockTransport]:
    transport = MockTransport()
    config = LoggerConfig(level=level, transports=[transport], **kwargs)
    return Logger(config), transport


class TestLogLevelFiltering:
    """Mirrors TS ServerLogger.test.ts 'log level filtering' suite."""

    def test_log_at_or_above_configured_level(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.info("TEST", "op", "info message")
        logger.warn("TEST", "op", "warn message")
        logger.error("TEST", "op", "error message")
        assert len(transport.logs) == 3
        assert transport.logs[0]["level"] == "INFO"
        assert transport.logs[1]["level"] == "WARN"
        assert transport.logs[2]["level"] == "ERROR"

    def test_filter_below_configured_level(self):
        logger, transport = _make_logger(LogLevel.WARN)
        logger.trace("TEST", "op", "trace")
        logger.debug("TEST", "op", "debug")
        logger.info("TEST", "op", "info")
        logger.warn("TEST", "op", "warn")
        logger.error("TEST", "op", "error")
        assert len(transport.logs) == 2
        assert transport.logs[0]["level"] == "WARN"
        assert transport.logs[1]["level"] == "ERROR"

    def test_allow_all_when_trace(self):
        logger, transport = _make_logger(LogLevel.TRACE)
        logger.trace("TEST", "op", "trace")
        logger.debug("TEST", "op", "debug")
        logger.info("TEST", "op", "info")
        logger.warn("TEST", "op", "warn")
        logger.error("TEST", "op", "error")
        assert len(transport.logs) == 5

    def test_only_error_when_error(self):
        logger, transport = _make_logger(LogLevel.ERROR)
        logger.trace("TEST", "op", "t")
        logger.debug("TEST", "op", "d")
        logger.info("TEST", "op", "i")
        logger.warn("TEST", "op", "w")
        logger.error("TEST", "op", "e")
        assert len(transport.logs) == 1
        assert transport.logs[0]["level"] == "ERROR"

    def test_filter_debug_when_info(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.debug("TEST", "op", "debug")
        assert len(transport.logs) == 0

    def test_allow_debug_when_debug(self):
        logger, transport = _make_logger(LogLevel.DEBUG)
        logger.debug("TEST", "op", "debug")
        assert len(transport.logs) == 1
        assert transport.logs[0]["level"] == "DEBUG"


class TestCategorySpecificLevels:
    """Mirrors TS 'category-specific log levels' suite."""

    def test_use_category_level_when_configured(self):
        logger, transport = _make_logger(
            LogLevel.ERROR,
            category_levels={"DATABASE": LogLevel.DEBUG},
        )
        logger.debug("DATABASE", "query", "debug database query")
        logger.debug("HTTP", "request", "debug http request")
        logger.error("HTTP", "request", "error http request")
        assert len(transport.logs) == 2
        assert transport.logs[0]["category"] == "DATABASE"
        assert transport.logs[0]["level"] == "DEBUG"
        assert transport.logs[1]["category"] == "HTTP"
        assert transport.logs[1]["level"] == "ERROR"

    def test_multiple_category_overrides(self):
        logger, transport = _make_logger(
            LogLevel.INFO,
            category_levels={
                "DATABASE": LogLevel.DEBUG,
                "AUTH": LogLevel.TRACE,
                "METRICS": LogLevel.WARN,
            },
        )
        logger.debug("DATABASE", "op", "msg")
        logger.trace("DATABASE", "op", "msg")  # filtered
        logger.trace("AUTH", "op", "msg")
        logger.info("METRICS", "op", "msg")  # filtered
        logger.warn("METRICS", "op", "msg")
        logger.info("OTHER", "op", "msg")
        logger.debug("OTHER", "op", "msg")  # filtered
        assert len(transport.logs) == 4
        assert [log["category"] for log in transport.logs] == [
            "DATABASE", "AUTH", "METRICS", "OTHER"
        ]

    def test_category_more_restrictive_than_default(self):
        logger, transport = _make_logger(
            LogLevel.DEBUG,
            category_levels={"NOISY": LogLevel.ERROR},
        )
        logger.debug("NOISY", "op", "msg")
        logger.info("NOISY", "op", "msg")
        logger.warn("NOISY", "op", "msg")
        logger.error("NOISY", "op", "msg")
        logger.debug("OTHER", "op", "msg")
        assert len(transport.logs) == 2
        assert transport.logs[0]["category"] == "NOISY"
        assert transport.logs[0]["level"] == "ERROR"
        assert transport.logs[1]["category"] == "OTHER"
        assert transport.logs[1]["level"] == "DEBUG"


class TestRuntimeConfigChanges:
    """Mirrors TS 'runtime configuration changes' suite."""

    def test_respect_level_changes_via_configure(self):
        logger, transport = _make_logger(LogLevel.ERROR)
        logger.info("TEST", "op", "msg1")
        assert len(transport.logs) == 0
        logger.configure(level=LogLevel.INFO)
        logger.info("TEST", "op", "msg2")
        assert len(transport.logs) == 1
        assert transport.logs[0]["message"] == "msg2"

    def test_respect_category_levels_via_configure(self):
        logger, transport = _make_logger(LogLevel.ERROR)
        logger.debug("DATABASE", "op", "msg1")
        assert len(transport.logs) == 0
        logger.configure(category_levels={"DATABASE": LogLevel.DEBUG})
        logger.debug("DATABASE", "op", "msg2")
        assert len(transport.logs) == 1
        assert transport.logs[0]["message"] == "msg2"


class TestStructuredLogOutput:
    def test_log_has_required_fields(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.info("AUTH", "login", "User logged in")
        log = transport.logs[0]
        assert log["timestamp"]  # non-empty string
        assert log["level"] == "INFO"
        assert log["category"] == "AUTH"
        assert log["operation"] == "login"
        assert log["message"] == "User logged in"
        assert log["environment"] == "server"

    def test_log_includes_data(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.info("TEST", "op", "msg", {"key": "value"})
        assert transport.logs[0]["data"] == {"key": "value"}

    def test_error_log_formats_exception(self):
        logger, transport = _make_logger(LogLevel.ERROR)
        try:
            raise ValueError("test error")
        except ValueError as e:
            logger.error("TEST", "op", "failed", e)
        log = transport.logs[0]
        assert log["error"]["name"] == "ValueError"
        assert log["error"]["message"] == "test error"

    def test_log_includes_metadata(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.info("TEST", "op", "msg")
        metadata = transport.logs[0].get("metadata", {})
        assert "hostname" in metadata
        assert "pid" in metadata

    def test_sanitizes_sensitive_data(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.info("TEST", "op", "msg", {"password": "secret", "name": "ok"})
        assert transport.logs[0]["data"]["password"] == "[REDACTED]"
        assert transport.logs[0]["data"]["name"] == "ok"


class TestRequestAndConnectionIds:
    def test_set_and_get_request_id(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.set_request_id("req-123")
        assert logger.get_request_id() == "req-123"
        logger.info("TEST", "op", "msg")
        assert transport.logs[0].get("request_id") == "req-123"

    def test_clear_request_id(self):
        logger, _ = _make_logger(LogLevel.INFO)
        logger.set_request_id("req-123")
        logger.clear_request_id()
        assert logger.get_request_id() is None

    def test_set_connection_id(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.set_connection_id("conn-456")
        logger.info("TEST", "op", "msg")
        assert transport.logs[0].get("connection_id") == "conn-456"


class TestChildLogger:
    def test_child_inherits_config(self):
        logger, transport = _make_logger(LogLevel.DEBUG)
        child = logger.child(request_id="req-child")
        child.debug("TEST", "op", "from child")
        assert len(transport.logs) == 1
        assert transport.logs[0].get("request_id") == "req-child"

    def test_child_does_not_affect_parent(self):
        logger, transport = _make_logger(LogLevel.INFO)
        logger.child(request_id="req-child")  # create child; should not affect parent
        logger.info("TEST", "op", "from parent")
        assert transport.logs[0].get("request_id") is None
