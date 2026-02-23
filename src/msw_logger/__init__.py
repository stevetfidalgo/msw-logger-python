"""msw-logger — Structured logging for Python server applications.

Usage:
    from msw_logger import logger, LogCat

    logger.info(LogCat.AUTH, "login", "User logged in", {"user_id": "123"})
"""

from .types import (
    DatadogConfig,
    ErrorDetails,
    LogCat,
    LogFormat,
    LoggerConfig,
    LogLevel,
    LogTransport,
    StructuredLog,
)
from .utils import (
    format_error,
    generate_request_id,
    get_current_timestamp,
    safe_stringify,
    sanitize_data,
    should_log,
)
from .config import create_default_config, create_transport, parse_log_format
from .logger import Logger
from .transports import ConsoleTransport, DatadogTransport

__all__ = [
    # Logger
    "logger",
    "create_logger",
    "Logger",
    # Types
    "LogLevel",
    "LogFormat",
    "LogCat",
    "StructuredLog",
    "ErrorDetails",
    "LogTransport",
    "LoggerConfig",
    "DatadogConfig",
    # Transports
    "ConsoleTransport",
    "DatadogTransport",
    # Config
    "create_default_config",
    "create_transport",
    "parse_log_format",
    # Utils
    "generate_request_id",
    "safe_stringify",
    "format_error",
    "should_log",
    "get_current_timestamp",
    "sanitize_data",
]


def create_logger(config: LoggerConfig | None = None, **kwargs) -> Logger:
    """Create a new Logger instance with custom configuration.

    Args:
        config: Full LoggerConfig, or pass keyword args.
    """
    if config is None and kwargs:
        config = LoggerConfig(**kwargs)
    return Logger(config)


# --- Lazy singleton ---
# On first attribute access (e.g. logger.info), creates a Logger instance.

class _LazyLogger:
    """Proxy that creates a Logger on first attribute access."""

    def __init__(self):
        self._instance = None

    def _get_instance(self):
        if self._instance is None:
            from .logger import Logger
            self._instance = Logger()
        return self._instance

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)


logger: Logger = _LazyLogger()  # type: ignore[assignment]
