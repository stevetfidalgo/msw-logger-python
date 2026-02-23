"""Tests for configuration module."""

import os
from unittest.mock import patch

from msw_logger.config import (
    create_default_config,
    create_transport,
    parse_category_levels,
    parse_log_format,
    parse_log_level,
)
from msw_logger.types import LogLevel


class TestParseLogLevel:
    def test_default_to_info_when_none(self):
        assert parse_log_level(None) == LogLevel.INFO

    def test_parse_trace(self):
        assert parse_log_level("TRACE") == LogLevel.TRACE

    def test_parse_debug(self):
        assert parse_log_level("DEBUG") == LogLevel.DEBUG

    def test_parse_info(self):
        assert parse_log_level("INFO") == LogLevel.INFO

    def test_parse_warn(self):
        assert parse_log_level("WARN") == LogLevel.WARN

    def test_parse_error(self):
        assert parse_log_level("ERROR") == LogLevel.ERROR

    def test_case_insensitive(self):
        assert parse_log_level("debug") == LogLevel.DEBUG

    def test_mixed_case(self):
        assert parse_log_level("DeBuG") == LogLevel.DEBUG

    def test_invalid_defaults_to_info(self):
        assert parse_log_level("INVALID") == LogLevel.INFO


class TestParseCategoryLevels:
    def test_none_returns_none(self):
        assert parse_category_levels(None) is None

    def test_empty_returns_none(self):
        assert parse_category_levels("") is None

    def test_single_category(self):
        result = parse_category_levels("DATABASE:DEBUG")
        assert result == {"DATABASE": LogLevel.DEBUG}

    def test_multiple_categories(self):
        result = parse_category_levels("DATABASE:DEBUG,AUTH:TRACE,HTTP:WARN")
        assert result == {
            "DATABASE": LogLevel.DEBUG,
            "AUTH": LogLevel.TRACE,
            "HTTP": LogLevel.WARN,
        }

    def test_handles_spaces(self):
        result = parse_category_levels("DATABASE : DEBUG , AUTH : TRACE")
        assert result == {"DATABASE": LogLevel.DEBUG, "AUTH": LogLevel.TRACE}

    def test_case_insensitive_levels(self):
        result = parse_category_levels("DATABASE:debug,AUTH:Trace")
        assert result == {"DATABASE": LogLevel.DEBUG, "AUTH": LogLevel.TRACE}


class TestParseLogFormat:
    def test_default_to_pretty_when_none(self):
        assert parse_log_format(None) == "pretty"

    def test_parse_pretty(self):
        assert parse_log_format("pretty") == "pretty"

    def test_parse_json(self):
        assert parse_log_format("json") == "json"

    def test_case_insensitive(self):
        assert parse_log_format("JSON") == "json"

    def test_mixed_case(self):
        assert parse_log_format("Pretty") == "pretty"

    def test_invalid_defaults_to_pretty(self):
        assert parse_log_format("xml") == "pretty"


class TestCreateDefaultConfig:
    def test_defaults_when_no_env_vars(self):
        with patch.dict(os.environ, {}, clear=True):
            config = create_default_config()
        assert config.level == LogLevel.INFO
        assert len(config.transports) == 1
        assert config.transports[0].name == "console"
        assert config.category_levels is None

    def test_reads_log_level(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            config = create_default_config()
        assert config.level == LogLevel.DEBUG

    def test_reads_category_levels(self):
        with patch.dict(
            os.environ,
            {"LOG_CATEGORY_LEVELS": "DATABASE:DEBUG,AUTH:TRACE"},
            clear=True,
        ):
            config = create_default_config()
        assert config.category_levels == {
            "DATABASE": LogLevel.DEBUG,
            "AUTH": LogLevel.TRACE,
        }

    def test_reads_transport_console(self):
        with patch.dict(os.environ, {"LOG_TRANSPORT_SERVER": "console"}, clear=True):
            config = create_default_config()
        assert config.transports[0].name == "console"

    def test_defaults_to_console_for_invalid_transport(self):
        with patch.dict(os.environ, {"LOG_TRANSPORT_SERVER": "invalid"}, clear=True):
            config = create_default_config()
        assert config.transports[0].name == "console"

    def test_reads_log_format(self):
        with patch.dict(os.environ, {"LOG_FORMAT_SERVER": "json"}, clear=True):
            config = create_default_config()
        assert config.format == "json"


class TestCreateTransport:
    def test_create_console(self):
        transport = create_transport("console")
        assert transport.name == "console"

    def test_unknown_falls_back_to_console(self):
        transport = create_transport("unknown")
        assert transport.name == "console"
