"""Logger implementation.

Single Logger class for server-side Python applications.
"""

from __future__ import annotations

import os
import socket
from typing import Any

from .config import create_default_config
from .types import LogLevel, LoggerConfig, StructuredLog
from .utils import format_error, get_current_timestamp, sanitize_data, should_log


class Logger:
    """Structured logger with configurable transports.

    Usage:
        logger = Logger()
        logger.info("AUTH", "login", "User logged in", {"user_id": "123"})
    """

    def __init__(self, config: LoggerConfig | None = None) -> None:
        self._config = config or create_default_config()
        self._request_id: str | None = self._config.default_request_id
        self._connection_id: str | None = self._config.default_connection_id

    # --- Request/Connection ID management ---

    def set_request_id(self, request_id: str) -> None:
        self._request_id = request_id

    def get_request_id(self) -> str | None:
        return self._request_id

    def clear_request_id(self) -> None:
        self._request_id = None

    def set_connection_id(self, connection_id: str) -> None:
        self._connection_id = connection_id

    def get_connection_id(self) -> str | None:
        return self._connection_id

    def clear_connection_id(self) -> None:
        self._connection_id = None

    # --- Core logging ---

    def _log(
        self,
        level: LogLevel,
        category: str,
        operation: str,
        message: str,
        data_or_error: dict[str, Any] | BaseException | None = None,
    ) -> None:
        if not should_log(level, self._config.level, category, self._config.category_levels):
            return

        log: StructuredLog = {
            "timestamp": get_current_timestamp(),
            "level": level.name,
            "category": category,
            "operation": operation,
            "message": message,
            "environment": "server",
        }

        if self._config.default_module:
            log["module"] = self._config.default_module
        if self._request_id:
            log["request_id"] = self._request_id
        if self._connection_id:
            log["connection_id"] = self._connection_id

        # Handle data vs error
        if data_or_error is not None:
            if isinstance(data_or_error, BaseException):
                log["error"] = format_error(
                    data_or_error, include_stack=self._config.include_stack_traces
                )
            else:
                log["data"] = sanitize_data(data_or_error)

        # Server metadata
        log["metadata"] = {
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
        }

        # Dispatch to transports
        for transport in self._config.transports:
            try:
                transport.log(log)
            except Exception as e:
                import sys

                print(f"[Logger] Transport {transport.name} failed: {e}", file=sys.stderr)

    # --- Level methods ---

    def trace(self, category: str, operation: str, message: str, data: dict[str, Any] | None = None) -> None:
        self._log(LogLevel.TRACE, category, operation, message, data)

    def debug(self, category: str, operation: str, message: str, data: dict[str, Any] | None = None) -> None:
        self._log(LogLevel.DEBUG, category, operation, message, data)

    def info(self, category: str, operation: str, message: str, data: dict[str, Any] | None = None) -> None:
        self._log(LogLevel.INFO, category, operation, message, data)

    def warn(self, category: str, operation: str, message: str, data: dict[str, Any] | None = None) -> None:
        self._log(LogLevel.WARN, category, operation, message, data)

    def error(
        self,
        category: str,
        operation: str,
        message: str,
        data_or_error: dict[str, Any] | BaseException | None = None,
    ) -> None:
        self._log(LogLevel.ERROR, category, operation, message, data_or_error)

    # --- Child logger ---

    def child(
        self,
        request_id: str | None = None,
        connection_id: str | None = None,
        module: str | None = None,
    ) -> Logger:
        """Create a child logger that shares transports but has its own context."""
        child_config = LoggerConfig(
            level=self._config.level,
            transports=self._config.transports,
            category_levels=self._config.category_levels,
            default_module=module or self._config.default_module,
            include_stack_traces=self._config.include_stack_traces,
            max_data_depth=self._config.max_data_depth,
            max_data_length=self._config.max_data_length,
        )
        child_logger = Logger(child_config)
        if request_id:
            child_logger.set_request_id(request_id)
        if connection_id:
            child_logger.set_connection_id(connection_id)
        return child_logger

    # --- Configuration ---

    def configure(self, **kwargs: Any) -> None:
        """Update logger configuration at runtime."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def flush(self) -> None:
        for transport in self._config.transports:
            if hasattr(transport, "flush"):
                transport.flush()

    def close(self) -> None:
        for transport in self._config.transports:
            if hasattr(transport, "close"):
                transport.close()
