"""Datadog transport — sends logs via HTTP API."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import DatadogConfig, StructuredLog


class DatadogTransport:
    """Datadog transport for sending logs to Datadog."""

    name = "datadog"

    def __init__(self, config: DatadogConfig) -> None:
        self._config = config

    def log(self, entry: StructuredLog) -> None:
        pass  # Stub — full implementation in Task 8

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass
