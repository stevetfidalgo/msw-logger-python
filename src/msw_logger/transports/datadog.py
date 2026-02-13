"""Datadog transport — sends logs via HTTP API.

Uses urllib from stdlib (no external dependencies for the transport itself).
Install `datadog-api-client` for richer integration, but the basic HTTP
transport works without it.
"""

from __future__ import annotations

import json
import socket
import sys
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..types import DatadogConfig, StructuredLog

_LEVEL_MAP = {
    "TRACE": "debug",
    "DEBUG": "debug",
    "INFO": "info",
    "WARN": "warn",
    "ERROR": "error",
}


class DatadogTransport:
    """Datadog transport that sends logs via HTTP Logs API."""

    name = "datadog"

    def __init__(self, config: DatadogConfig) -> None:
        self._config = config
        self._url = f"https://http-intake.logs.{config.site}/api/v2/logs"
        self._hostname = socket.gethostname()

    def log(self, entry: StructuredLog) -> None:
        level = entry.get("level", "INFO")

        payload: dict[str, Any] = {
            "ddsource": self._config.source,
            "ddtags": f"env:{self._config.env},service:{self._config.service}",
            "hostname": self._hostname,
            "message": entry.get("message", ""),
            "status": _LEVEL_MAP.get(level, "info"),
            "timestamp": entry.get("timestamp", ""),
            "category": entry.get("category", ""),
            "operation": entry.get("operation", ""),
        }

        if entry.get("request_id"):
            payload["request_id"] = entry["request_id"]
        if entry.get("connection_id"):
            payload["connection_id"] = entry["connection_id"]
        if entry.get("data"):
            payload["data"] = entry["data"]
        if entry.get("error"):
            payload["error"] = entry["error"]

        body = json.dumps([payload]).encode("utf-8")
        request = urllib.request.Request(
            self._url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "DD-API-KEY": self._config.api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                response.read()
        except Exception as e:
            print(f"[Datadog] Failed to send log: {e}", file=sys.stderr)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass
