"""Console transport — ANSI-colored terminal output."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import StructuredLog


class ConsoleTransport:
    """Console transport for pretty-printed log output."""

    name = "console"

    def log(self, entry: StructuredLog) -> None:
        pass  # Stub — full implementation in Task 6

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass
