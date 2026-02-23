"""Console transport — ANSI-colored terminal output."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ..utils import safe_stringify

if TYPE_CHECKING:
    from ..types import LogFormat, StructuredLog

# ANSI color codes
_RESET = "\x1b[0m"
_BRIGHT = "\x1b[1m"
_DIM = "\x1b[2m"
_RED = "\x1b[31m"
_YELLOW = "\x1b[33m"
_BLUE = "\x1b[34m"
_MAGENTA = "\x1b[35m"
_CYAN = "\x1b[36m"
_WHITE = "\x1b[37m"

_LEVEL_COLORS = {
    "TRACE": _DIM + _CYAN,
    "DEBUG": _DIM + _WHITE,
    "INFO": _BLUE,
    "WARN": _YELLOW,
    "ERROR": _RED,
}


class ConsoleTransport:
    """Console transport for pretty-printed log output.

    Detects TTY and uses ANSI colors when available, plain text otherwise.
    """

    name = "console"

    def __init__(self, format: LogFormat = "pretty") -> None:
        self._format = format
        self._use_colors = sys.stdout.isatty()

    def log(self, entry: StructuredLog) -> None:
        level = entry.get("level", "INFO")
        output = self._format_pretty(entry)

        if level in ("WARN", "ERROR"):
            print(output, file=sys.stderr, end="")
        else:
            print(output, file=sys.stdout, end="")

    def _format_pretty(self, entry: StructuredLog) -> str:
        timestamp = entry.get("timestamp", "")
        level = entry.get("level", "INFO")
        category = entry.get("category", "")
        operation = entry.get("operation", "")
        message = entry.get("message", "")
        data = entry.get("data")
        error = entry.get("error")
        request_id = entry.get("request_id")
        connection_id = entry.get("connection_id")

        c = self._use_colors
        level_color = _LEVEL_COLORS.get(level, _WHITE)

        lines: list[str] = []

        # Header line
        if c:
            lines.append(
                f"{_DIM}[{timestamp}]{_RESET} "
                f"{level_color}{level}{_RESET} "
                f"{_MAGENTA}[{category}]{_RESET} "
                f"{_CYAN}{operation}{_RESET}"
            )
        else:
            lines.append(f"[{timestamp}] {level} [{category}] {operation}")

        # Message
        if c:
            lines.append(f"  {_BRIGHT}Message:{_RESET} {message}")
        else:
            lines.append(f"  Message: {message}")

        # IDs
        if request_id:
            lines.append(f"  Request ID: {request_id}")
        if connection_id:
            lines.append(f"  Connection ID: {connection_id}")

        # Data
        if data and isinstance(data, dict) and data:
            if c:
                lines.append(f"  {_BRIGHT}Data:{_RESET}")
            else:
                lines.append("  Data:")
            data_str = safe_stringify(data, 5, 5000)
            for line in data_str.split("\n"):
                lines.append(f"    {line}")

        # Error
        if error:
            err_name = error.get("name", "Error")
            err_msg = error.get("message", "")
            if c:
                lines.append(
                    f"  {_RED}{_BRIGHT}Error:{_RESET} {_RED}{err_name}: {err_msg}{_RESET}"
                )
            else:
                lines.append(f"  Error: {err_name}: {err_msg}")

            if error.get("code"):
                lines.append(f"  Error Code: {error['code']}")

            if error.get("stack"):
                for stack_line in error["stack"].split("\n")[1:]:
                    if stack_line.strip():
                        if c:
                            lines.append(f"    {_DIM}{stack_line}{_RESET}")
                        else:
                            lines.append(f"    {stack_line}")

            if error.get("context"):
                lines.append("  Error Context:")
                ctx_str = safe_stringify(error["context"], 3, 2000)
                for ctx_line in ctx_str.split("\n"):
                    lines.append(f"    {ctx_line}")

        return "\n".join(lines) + "\n"

    def flush(self) -> None:
        sys.stdout.flush()
        sys.stderr.flush()

    def close(self) -> None:
        pass
