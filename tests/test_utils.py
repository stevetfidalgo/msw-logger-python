"""Tests for utility functions."""

from msw_logger.types import LogLevel
from msw_logger.utils import (
    format_error,
    generate_request_id,
    safe_stringify,
    sanitize_data,
    should_log,
)


class TestShouldLog:
    """Tests for should_log() — mirrors TS utils.test.ts."""

    # Basic level filtering
    def test_allow_error_when_level_is_error(self):
        assert should_log(LogLevel.ERROR, LogLevel.ERROR) is True

    def test_block_warn_when_level_is_error(self):
        assert should_log(LogLevel.WARN, LogLevel.ERROR) is False

    def test_block_info_when_level_is_error(self):
        assert should_log(LogLevel.INFO, LogLevel.ERROR) is False

    def test_block_debug_when_level_is_error(self):
        assert should_log(LogLevel.DEBUG, LogLevel.ERROR) is False

    def test_block_trace_when_level_is_error(self):
        assert should_log(LogLevel.TRACE, LogLevel.ERROR) is False

    # WARN level
    def test_allow_error_when_level_is_warn(self):
        assert should_log(LogLevel.ERROR, LogLevel.WARN) is True

    def test_allow_warn_when_level_is_warn(self):
        assert should_log(LogLevel.WARN, LogLevel.WARN) is True

    def test_block_info_when_level_is_warn(self):
        assert should_log(LogLevel.INFO, LogLevel.WARN) is False

    # INFO level
    def test_allow_info_when_level_is_info(self):
        assert should_log(LogLevel.INFO, LogLevel.INFO) is True

    def test_block_debug_when_level_is_info(self):
        assert should_log(LogLevel.DEBUG, LogLevel.INFO) is False

    def test_block_trace_when_level_is_info(self):
        assert should_log(LogLevel.TRACE, LogLevel.INFO) is False

    # DEBUG level
    def test_allow_debug_and_above_when_level_is_debug(self):
        assert should_log(LogLevel.ERROR, LogLevel.DEBUG) is True
        assert should_log(LogLevel.WARN, LogLevel.DEBUG) is True
        assert should_log(LogLevel.INFO, LogLevel.DEBUG) is True
        assert should_log(LogLevel.DEBUG, LogLevel.DEBUG) is True

    def test_block_trace_when_level_is_debug(self):
        assert should_log(LogLevel.TRACE, LogLevel.DEBUG) is False

    # TRACE level
    def test_allow_all_when_level_is_trace(self):
        for level in LogLevel:
            assert should_log(level, LogLevel.TRACE) is True

    # Category-specific overrides
    def test_use_category_level_when_specified(self):
        category_levels = {"DATABASE": LogLevel.DEBUG}
        assert should_log(LogLevel.DEBUG, LogLevel.ERROR, "DATABASE", category_levels) is True
        assert should_log(LogLevel.TRACE, LogLevel.ERROR, "DATABASE", category_levels) is False

    def test_use_default_when_category_not_in_overrides(self):
        category_levels = {"DATABASE": LogLevel.DEBUG}
        assert should_log(LogLevel.DEBUG, LogLevel.ERROR, "API", category_levels) is False
        assert should_log(LogLevel.ERROR, LogLevel.ERROR, "API", category_levels) is True

    def test_use_default_when_no_category_provided(self):
        category_levels = {"DATABASE": LogLevel.DEBUG}
        assert should_log(LogLevel.DEBUG, LogLevel.ERROR, None, category_levels) is False
        assert should_log(LogLevel.ERROR, LogLevel.ERROR, None, category_levels) is True

    def test_handle_multiple_category_overrides(self):
        category_levels = {
            "DATABASE": LogLevel.DEBUG,
            "AUTH": LogLevel.TRACE,
            "HTTP": LogLevel.WARN,
        }
        assert should_log(LogLevel.DEBUG, LogLevel.INFO, "DATABASE", category_levels) is True
        assert should_log(LogLevel.TRACE, LogLevel.INFO, "DATABASE", category_levels) is False
        assert should_log(LogLevel.TRACE, LogLevel.INFO, "AUTH", category_levels) is True
        assert should_log(LogLevel.INFO, LogLevel.INFO, "HTTP", category_levels) is False
        assert should_log(LogLevel.WARN, LogLevel.INFO, "HTTP", category_levels) is True

    def test_work_with_none_category_levels(self):
        assert should_log(LogLevel.INFO, LogLevel.INFO, "DATABASE", None) is True
        assert should_log(LogLevel.DEBUG, LogLevel.INFO, "DATABASE", None) is False

    def test_work_with_empty_category_levels(self):
        assert should_log(LogLevel.INFO, LogLevel.INFO, "DATABASE", {}) is True
        assert should_log(LogLevel.DEBUG, LogLevel.INFO, "DATABASE", {}) is False


class TestGenerateRequestId:
    def test_returns_uuid_string(self):
        rid = generate_request_id()
        assert isinstance(rid, str)
        assert len(rid) == 36
        assert rid.count("-") == 4

    def test_generates_unique_ids(self):
        ids = {generate_request_id() for _ in range(100)}
        assert len(ids) == 100


class TestSafeStringify:
    def test_stringify_dict(self):
        result = safe_stringify({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result

    def test_stringify_none(self):
        assert safe_stringify(None) == "null"

    def test_stringify_string(self):
        assert safe_stringify("hello") == "hello"

    def test_stringify_number(self):
        assert safe_stringify(42) == "42"

    def test_truncate_long_output(self):
        result = safe_stringify({"data": "x" * 200}, max_length=100)
        assert len(result) <= 115  # 100 + "... [Truncated]"
        assert "[Truncated]" in result

    def test_handle_circular_reference(self):
        d: dict = {}
        d["self"] = d
        result = safe_stringify(d)
        assert "[Circular Reference]" in result

    def test_depth_limiting(self):
        nested = {"a": {"b": {"c": {"d": {"e": {"f": "deep"}}}}}}
        result = safe_stringify(nested, max_depth=3)
        assert "[Max Depth]" in result


class TestSanitizeData:
    def test_redact_password(self):
        result = sanitize_data({"password": "secret123", "username": "alice"})
        assert result["password"] == "[REDACTED]"
        assert result["username"] == "alice"

    def test_redact_token(self):
        result = sanitize_data({"auth_token": "abc", "name": "test"})
        assert result["auth_token"] == "[REDACTED]"
        assert result["name"] == "test"

    def test_redact_nested(self):
        result = sanitize_data({"config": {"api_key": "secret", "host": "localhost"}})
        assert result["config"]["api_key"] == "[REDACTED]"
        assert result["config"]["host"] == "localhost"

    def test_case_insensitive_matching(self):
        result = sanitize_data({"Password": "x", "API_KEY": "y"})
        assert result["Password"] == "[REDACTED]"
        assert result["API_KEY"] == "[REDACTED]"

    def test_preserve_non_sensitive(self):
        data = {"count": 5, "items": [1, 2, 3]}
        result = sanitize_data(data)
        assert result == data


class TestFormatError:
    def test_format_exception(self):
        try:
            raise ValueError("test error")
        except ValueError as e:
            result = format_error(e)
        assert result["name"] == "ValueError"
        assert result["message"] == "test error"
        assert "stack" in result

    def test_format_exception_without_stack(self):
        try:
            raise TypeError("bad type")
        except TypeError as e:
            result = format_error(e, include_stack=False)
        assert result["name"] == "TypeError"
        assert "stack" not in result

    def test_format_string_error(self):
        result = format_error("something went wrong")
        assert result["name"] == "Error"
        assert result["message"] == "something went wrong"

    def test_format_unknown_error(self):
        result = format_error(42)
        assert result["name"] == "UnknownError"
        assert result["message"] == "42"
