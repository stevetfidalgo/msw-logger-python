"""Core types for the structured logging system."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol, TypedDict, runtime_checkable


class LogLevel(enum.IntEnum):
    """Log severity levels following standard logging conventions."""

    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


class LogCat:
    """Log categories for consistent classification.

    These are example categories for common server application patterns.
    Define your own categories specific to your application domain.

    Usage:
        logger.info(LogCat.AUTH, "login", "User logged in")

        # Or define custom categories:
        class MyLogCat:
            PAYMENT = "PAYMENT"
            CART = "CART"
    """

    # Server Categories
    HTTP_REQUEST = "HTTP_REQUEST"
    HTTP_RESPONSE = "HTTP_RESPONSE"
    MIDDLEWARE = "MIDDLEWARE"
    DATABASE = "DATABASE"
    MIGRATION = "MIGRATION"
    SERVICE = "SERVICE"
    WORKFLOW = "WORKFLOW"
    SECURITY = "SECURITY"
    EXTERNAL_API = "EXTERNAL_API"
    EMAIL = "EMAIL"
    SMS = "SMS"
    JOB = "JOB"
    CRON = "CRON"
    CACHE = "CACHE"
    FILE_SYSTEM = "FILE_SYSTEM"
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"
    HEALTH = "HEALTH"

    # Universal Categories
    AUTH = "AUTH"
    VALIDATION = "VALIDATION"
    WEBSOCKET = "WEBSOCKET"
    API_CALL = "API_CALL"


class ErrorDetails(TypedDict, total=False):
    """Structured error information."""

    name: str  # required
    message: str  # required
    stack: str
    code: str | int
    context: dict[str, Any]


class StructuredLog(TypedDict, total=False):
    """Core structured log entry. Canonical format all transports receive."""

    timestamp: str  # required - ISO 8601
    level: str  # required - LogLevel name
    category: str  # required
    operation: str  # required
    message: str  # required
    environment: str  # required - always "server" for Python
    module: str
    request_id: str
    session_id: str
    connection_id: str
    data: dict[str, Any]
    error: ErrorDetails
    metadata: dict[str, Any]


@runtime_checkable
class LogTransport(Protocol):
    """Transport interface that all log transports must implement."""

    name: str

    def log(self, entry: StructuredLog) -> None: ...

    def flush(self) -> None: ...

    def close(self) -> None: ...


@dataclass
class LoggerConfig:
    """Logger configuration."""

    level: LogLevel = LogLevel.INFO
    transports: list[Any] = field(default_factory=list)
    category_levels: dict[str, LogLevel] | None = None
    default_request_id: str | None = None
    default_connection_id: str | None = None
    default_module: str | None = None
    include_stack_traces: bool = True
    max_data_depth: int = 5
    max_data_length: int = 10000


@dataclass
class DatadogConfig:
    """Datadog transport configuration."""

    api_key: str
    service: str = "app"
    env: str = "development"
    site: str = "datadoghq.com"
    source: str = "python"
