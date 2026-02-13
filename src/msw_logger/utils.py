"""Logging utility functions.

Helpers for UUID generation, safe serialization, error formatting,
log level filtering, and data sanitization.
"""

from __future__ import annotations

import json
import traceback
import uuid
from typing import Any

from .types import ErrorDetails, LogLevel

# Sensitive field names for sanitization (case-insensitive matching)
_SENSITIVE_KEYS = [
    "password",
    "token",
    "apikey",
    "api_key",
    "secret",
    "authorization",
    "auth",
    "accesstoken",
    "access_token",
    "refreshtoken",
    "refresh_token",
    "privatekey",
    "private_key",
]


def generate_request_id() -> str:
    """Generate a UUID v4 for request ID correlation."""
    return str(uuid.uuid4())


def should_log(
    message_level: LogLevel,
    configured_level: LogLevel,
    category: str | None = None,
    category_levels: dict[str, LogLevel] | None = None,
) -> bool:
    """Determine if a log should be output based on configured level.

    Uses category-specific level if configured, otherwise the default level.
    """
    effective_level = configured_level
    if category and category_levels and category in category_levels:
        effective_level = category_levels[category]
    return message_level >= effective_level


def safe_stringify(
    obj: Any,
    max_depth: int = 5,
    max_length: int = 10000,
) -> str:
    """Safely serialize an object to JSON string.

    Handles circular references via id() tracking and limits depth/length.
    """
    if obj is None:
        return "null"
    if not isinstance(obj, (dict, list, tuple, set)):
        return str(obj)

    seen: set[int] = set()

    def _default(o: Any) -> Any:
        return str(o)

    def _limit_depth(o: Any, depth: int) -> Any:
        if isinstance(o, (str, int, float, bool)) or o is None:
            return o

        obj_id = id(o)
        if obj_id in seen:
            return "[Circular Reference]"

        if depth > max_depth:
            return "[Max Depth]"

        seen.add(obj_id)
        try:
            if isinstance(o, dict):
                return {k: _limit_depth(v, depth + 1) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                return [_limit_depth(item, depth + 1) for item in o]
            if isinstance(o, set):
                return [_limit_depth(item, depth + 1) for item in o]
            return str(o)
        finally:
            seen.discard(obj_id)

    try:
        cleaned = _limit_depth(obj, 0)
        result = json.dumps(cleaned, indent=2, default=_default)
        if len(result) > max_length:
            return result[:max_length] + "... [Truncated]"
        return result
    except Exception as e:
        return f"[Serialization Error: {e}]"


def sanitize_data(
    data: dict[str, Any],
    sensitive_keys: list[str] | None = None,
) -> dict[str, Any]:
    """Recursively redact sensitive fields from a data dict."""
    keys = sensitive_keys or _SENSITIVE_KEYS

    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        is_sensitive = any(sk in key.lower() for sk in keys)
        if is_sensitive:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_data(value, keys)
        else:
            sanitized[key] = value
    return sanitized


def format_error(error: Any, include_stack: bool = True) -> ErrorDetails:
    """Format an error into structured ErrorDetails."""
    if isinstance(error, BaseException):
        details = ErrorDetails(name=type(error).__name__, message=str(error))
        if include_stack:
            details["stack"] = "".join(traceback.format_exception(error))
        return details

    if isinstance(error, str):
        return ErrorDetails(name="Error", message=error)

    return ErrorDetails(name="UnknownError", message=str(error))


def get_current_timestamp() -> str:
    """Return current time as ISO 8601 UTC string."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
