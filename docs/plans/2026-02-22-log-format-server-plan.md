# LOG_FORMAT_SERVER + LOG_TRANSPORT_SERVER Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add JSON log format support via `LOG_FORMAT_SERVER` and rename `LOG_TRANSPORT` to `LOG_TRANSPORT_SERVER` for consistency with the TypeScript sister project.

**Architecture:** ConsoleTransport gains a `format` parameter (`"pretty"` | `"json"`). When `"json"`, it outputs `json.dumps(entry)` as a single line to stdout. Config reads `LOG_FORMAT_SERVER` env var and passes it through `create_transport()`. The `LOG_TRANSPORT` env var is renamed to `LOG_TRANSPORT_SERVER`.

**Tech Stack:** Python, pytest, ruff

---

### Task 1: Add LogFormat type and LoggerConfig.format field

**Files:**
- Modify: `src/msw_logger/types.py:1-7` (imports)
- Modify: `src/msw_logger/types.py:103-115` (LoggerConfig)

**Step 1: Add LogFormat type alias**

In `src/msw_logger/types.py`, add `Literal` to the typing import, and add after the `LogLevel` class:

```python
from typing import Any, Literal, Protocol, TypedDict, runtime_checkable

# ... after LogLevel class ...

LogFormat = Literal["pretty", "json"]
```

**Step 2: Add format field to LoggerConfig**

```python
@dataclass
class LoggerConfig:
    """Logger configuration."""

    level: LogLevel = LogLevel.INFO
    transports: list[Any] = field(default_factory=list)
    category_levels: dict[str, LogLevel] | None = None
    format: LogFormat = "pretty"
    default_request_id: str | None = None
    default_connection_id: str | None = None
    default_module: str | None = None
    include_stack_traces: bool = True
    max_data_depth: int = 5
    max_data_length: int = 10000
```

**Step 3: Run tests to verify no regressions**

Run: `pytest -x -q`
Expected: All 97 tests pass (no behavior change yet).

**Step 4: Commit**

```
feat: add LogFormat type and format field to LoggerConfig
```

---

### Task 2: Add parse_log_format() and rename LOG_TRANSPORT to LOG_TRANSPORT_SERVER

**Files:**
- Modify: `src/msw_logger/config.py:12` (imports)
- Modify: `src/msw_logger/config.py:53-104` (create_transport, create_default_config)
- Test: `tests/test_config.py`

**Step 1: Write failing tests for parse_log_format**

Add to `tests/test_config.py`:

```python
from msw_logger.config import (
    create_default_config,
    create_transport,
    parse_category_levels,
    parse_log_format,
    parse_log_level,
)


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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py::TestParseLogFormat -v`
Expected: FAIL — `parse_log_format` not importable.

**Step 3: Implement parse_log_format in config.py**

Add after `parse_log_level()`:

```python
from .types import DatadogConfig, LogFormat, LoggerConfig, LogLevel


def parse_log_format(value: str | None) -> LogFormat:
    """Parse log format from string. Defaults to pretty."""
    if not value:
        return "pretty"

    normalized = value.lower()
    if normalized in ("pretty", "json"):
        return normalized  # type: ignore[return-value]

    print(
        f'[Logger] Invalid LOG_FORMAT_SERVER "{value}", defaulting to pretty',
        file=sys.stderr,
    )
    return "pretty"
```

**Step 4: Run parse_log_format tests**

Run: `pytest tests/test_config.py::TestParseLogFormat -v`
Expected: All 6 pass.

**Step 5: Update create_transport() signature to accept format**

```python
def create_transport(transport_type: str, format: LogFormat = "pretty") -> Any:
    """Create a transport instance by type name.

    Returns ConsoleTransport for unknown types (with warning).
    """
    from .transports.console import ConsoleTransport

    normalized = transport_type.lower()

    if normalized == "console":
        return ConsoleTransport(format=format)

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
    return ConsoleTransport(format=format)
```

**Step 6: Rename LOG_TRANSPORT to LOG_TRANSPORT_SERVER and add LOG_FORMAT_SERVER**

In `create_default_config()`:

```python
def create_default_config() -> LoggerConfig:
    """Create logger configuration from environment variables."""
    level = parse_log_level(_get_env("LOG_LEVEL"))
    category_levels = parse_category_levels(_get_env("LOG_CATEGORY_LEVELS"))
    transport_type = _get_env("LOG_TRANSPORT_SERVER") or "console"
    format = parse_log_format(_get_env("LOG_FORMAT_SERVER"))

    try:
        transport = create_transport(transport_type, format=format)
    except Exception as e:
        print(f"[Logger] Failed to create {transport_type} transport: {e}", file=sys.stderr)
        from .transports.console import ConsoleTransport

        transport = ConsoleTransport(format=format)

    return LoggerConfig(
        level=level,
        transports=[transport],
        category_levels=category_levels,
        format=format,
        include_stack_traces=_get_env("LOG_INCLUDE_STACK_TRACES") != "false",
        max_data_depth=int(_get_env("LOG_MAX_DATA_DEPTH") or "5"),
        max_data_length=int(_get_env("LOG_MAX_DATA_LENGTH") or "10000"),
    )
```

**Step 7: Update existing tests — rename LOG_TRANSPORT to LOG_TRANSPORT_SERVER**

In `tests/test_config.py`, update:

```python
def test_reads_transport_console(self):
    with patch.dict(os.environ, {"LOG_TRANSPORT_SERVER": "console"}, clear=True):
        config = create_default_config()
    assert config.transports[0].name == "console"

def test_defaults_to_console_for_invalid_transport(self):
    with patch.dict(os.environ, {"LOG_TRANSPORT_SERVER": "invalid"}, clear=True):
        config = create_default_config()
    assert config.transports[0].name == "console"
```

Add new test for LOG_FORMAT_SERVER integration:

```python
def test_reads_log_format(self):
    with patch.dict(os.environ, {"LOG_FORMAT_SERVER": "json"}, clear=True):
        config = create_default_config()
    assert config.format == "json"
```

**Step 8: Run all config tests**

Run: `pytest tests/test_config.py -v`
Expected: All pass (some will fail until Task 3 updates ConsoleTransport constructor).

**Step 9: Commit**

```
feat: add parse_log_format, rename LOG_TRANSPORT to LOG_TRANSPORT_SERVER
```

---

### Task 3: Add JSON format support to ConsoleTransport

**Files:**
- Modify: `src/msw_logger/transports/console.py:1-6` (imports)
- Modify: `src/msw_logger/transports/console.py:33-51` (constructor and log method)
- Test: `tests/test_console_transport.py`

**Step 1: Write failing tests for JSON format**

Add to `tests/test_console_transport.py`:

```python
import json


class TestJsonFormat:
    def test_json_outputs_valid_json(self):
        transport = ConsoleTransport(format="json")
        log = _make_log("INFO")
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(log)
        output = mock_out.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"

    def test_json_is_single_line(self):
        transport = ConsoleTransport(format="json")
        log = _make_log("INFO", data={"key": "value"})
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(log)
        output = mock_out.getvalue()
        # Should be exactly one line (content + newline from print)
        assert output.count("\n") == 1

    def test_json_includes_all_fields(self):
        transport = ConsoleTransport(format="json")
        log = _make_log("INFO", request_id="req-123", data={"key": "value"})
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(log)
        parsed = json.loads(mock_out.getvalue())
        assert parsed["timestamp"] == "2025-01-15T10:30:00.000Z"
        assert parsed["level"] == "INFO"
        assert parsed["category"] == "TEST"
        assert parsed["operation"] == "test-operation"
        assert parsed["message"] == "Test message"
        assert parsed["environment"] == "server"
        assert parsed["request_id"] == "req-123"
        assert parsed["data"] == {"key": "value"}

    def test_json_routes_all_levels_to_stdout(self):
        """JSON mode always uses stdout (for log collectors), even for WARN/ERROR."""
        for level in ("TRACE", "DEBUG", "INFO", "WARN", "ERROR"):
            transport = ConsoleTransport(format="json")
            with patch("sys.stdout", new_callable=StringIO) as mock_out, \
                 patch("sys.stderr", new_callable=StringIO) as mock_err:
                transport.log(_make_log(level))
            assert mock_out.getvalue(), f"{level} should write to stdout"
            assert not mock_err.getvalue(), f"{level} should NOT write to stderr"

    def test_pretty_format_unchanged(self):
        """Explicit pretty format behaves like default."""
        transport = ConsoleTransport(format="pretty")
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            transport.log(_make_log("INFO"))
        output = mock_out.getvalue()
        assert "Message:" in output  # Pretty format has labels
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_console_transport.py::TestJsonFormat -v`
Expected: FAIL — ConsoleTransport doesn't accept `format` kwarg.

**Step 3: Implement JSON format in ConsoleTransport**

Update `src/msw_logger/transports/console.py`:

Add `json` import at top:

```python
import json
```

Add `TYPE_CHECKING` import for `LogFormat`:

```python
if TYPE_CHECKING:
    from ..types import LogFormat, StructuredLog
```

Update constructor and log method:

```python
class ConsoleTransport:
    """Console transport for pretty-printed or JSON log output.

    Detects TTY and uses ANSI colors when available, plain text otherwise.
    In JSON mode, outputs single-line JSON to stdout for log collectors.
    """

    name = "console"

    def __init__(self, format: LogFormat = "pretty") -> None:
        self._format = format
        self._use_colors = sys.stdout.isatty()

    def log(self, entry: StructuredLog) -> None:
        if self._format == "json":
            print(json.dumps(entry))
            return

        level = entry.get("level", "INFO")
        output = self._format_pretty(entry)

        if level in ("WARN", "ERROR"):
            print(output, file=sys.stderr, end="")
        else:
            print(output, file=sys.stdout, end="")
```

Rename `_format` method to `_format_pretty` (since `_format` is now an attribute):

```python
    def _format_pretty(self, entry: StructuredLog) -> str:
        # ... existing _format body unchanged ...
```

**Step 4: Run all console transport tests**

Run: `pytest tests/test_console_transport.py -v`
Expected: All pass (old tests + new JSON tests).

**Step 5: Run full test suite**

Run: `pytest -x -q`
Expected: All tests pass.

**Step 6: Commit**

```
feat: add JSON format support to ConsoleTransport
```

---

### Task 4: Update exports, .env.example, and README

**Files:**
- Modify: `src/msw_logger/__init__.py:9-17` (imports)
- Modify: `src/msw_logger/__init__.py:30-56` (__all__)
- Modify: `.env.example`
- Modify: `README.md:68-81`

**Step 1: Export LogFormat and parse_log_format**

In `src/msw_logger/__init__.py`, add to imports:

```python
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

from .config import create_default_config, create_transport, parse_log_format
```

Add to `__all__`:

```python
"LogFormat",
"parse_log_format",
```

**Step 2: Update .env.example**

```bash
# General Logging Configuration
LOG_LEVEL=INFO
LOG_TRANSPORT_SERVER=console
LOG_CATEGORY_LEVELS=

# Server-side log format (optional)
# pretty - Multi-line colored output for local development (default)
# json   - Single-line JSON for log collector agents (e.g., Datadog Agent sidecar)
# LOG_FORMAT_SERVER=pretty

# Datadog Configuration (if LOG_TRANSPORT_SERVER=datadog)
DATADOG_API_KEY=
DATADOG_SERVICE_NAME=
DATADOG_ENV=development
DATADOG_SITE=datadoghq.com
```

**Step 3: Update README.md env var section**

Update the Configuration section (~lines 68-81):

```bash
# General Logging Configuration
LOG_LEVEL=INFO                          # TRACE, DEBUG, INFO, WARN, ERROR
LOG_TRANSPORT_SERVER=console            # console, datadog

# Server-side log format (console transport only)
# LOG_FORMAT_SERVER=pretty              # pretty (default), json

# Category-Specific Log Levels (optional)
LOG_CATEGORY_LEVELS=DATABASE:DEBUG,AUTH:TRACE,HTTP:WARN

# Datadog Configuration (if LOG_TRANSPORT_SERVER=datadog)
DATADOG_API_KEY=your_api_key_here
DATADOG_SERVICE_NAME=my-app
DATADOG_ENV=development
DATADOG_SITE=datadoghq.com
```

**Step 4: Lint**

Run: `ruff check src/ tests/`
Expected: No errors.

**Step 5: Run full test suite**

Run: `pytest -x -q`
Expected: All tests pass.

**Step 6: Commit**

```
feat: update exports, docs, and .env.example for LOG_FORMAT_SERVER
```
