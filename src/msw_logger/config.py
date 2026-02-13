"""Logger configuration.

Reads configuration from environment variables and creates transports.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from .types import DatadogConfig, LoggerConfig, LogLevel


def _get_env(key: str) -> str | None:
    """Get environment variable value."""
    return os.environ.get(key)


def parse_log_level(value: str | None) -> LogLevel:
    """Parse log level from string. Defaults to INFO."""
    if not value:
        return LogLevel.INFO

    normalized = value.upper()
    try:
        return LogLevel[normalized]
    except KeyError:
        print(f'[Logger] Invalid LOG_LEVEL "{value}", defaulting to INFO', file=sys.stderr)
        return LogLevel.INFO


def parse_category_levels(value: str | None) -> dict[str, LogLevel] | None:
    """Parse category-specific log levels.

    Format: "CATEGORY1:LEVEL1,CATEGORY2:LEVEL2"
    """
    if not value:
        return None

    category_levels: dict[str, LogLevel] = {}
    for pair in value.split(","):
        parts = pair.split(":")
        if len(parts) == 2:
            category = parts[0].strip()
            level = parse_log_level(parts[1].strip())
            if category:
                category_levels[category] = level

    return category_levels if category_levels else None


def create_transport(transport_type: str) -> Any:
    """Create a transport instance by type name.

    Returns ConsoleTransport for unknown types (with warning).
    """
    from .transports.console import ConsoleTransport

    normalized = transport_type.lower()

    if normalized == "console":
        return ConsoleTransport()

    if normalized == "datadog":
        from .transports.datadog import DatadogTransport

        config = DatadogConfig(
            api_key=_get_env("DATADOG_API_KEY") or "",
            service=_get_env("DATADOG_SERVICE_NAME") or "app",
            env=_get_env("DATADOG_ENV") or "development",
            site=_get_env("DATADOG_SITE") or "datadoghq.com",
        )
        return DatadogTransport(config)

    print(
        f'[Logger] Unknown transport type "{transport_type}", falling back to console',
        file=sys.stderr,
    )
    return ConsoleTransport()


def create_default_config() -> LoggerConfig:
    """Create logger configuration from environment variables."""
    level = parse_log_level(_get_env("LOG_LEVEL"))
    category_levels = parse_category_levels(_get_env("LOG_CATEGORY_LEVELS"))
    transport_type = _get_env("LOG_TRANSPORT") or "console"

    try:
        transport = create_transport(transport_type)
    except Exception as e:
        print(f"[Logger] Failed to create {transport_type} transport: {e}", file=sys.stderr)
        from .transports.console import ConsoleTransport

        transport = ConsoleTransport()

    return LoggerConfig(
        level=level,
        transports=[transport],
        category_levels=category_levels,
        include_stack_traces=_get_env("LOG_INCLUDE_STACK_TRACES") != "false",
        max_data_depth=int(_get_env("LOG_MAX_DATA_DEPTH") or "5"),
        max_data_length=int(_get_env("LOG_MAX_DATA_LENGTH") or "10000"),
    )
