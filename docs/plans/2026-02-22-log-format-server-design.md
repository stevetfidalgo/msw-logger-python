# LOG_FORMAT_SERVER + LOG_TRANSPORT_SERVER Rename

## Summary

Port the `LOG_FORMAT_SERVER` feature from the TypeScript sister project (`~/msw-logger`) and rename `LOG_TRANSPORT` to `LOG_TRANSPORT_SERVER` for consistency.

## Changes

### 1. New type: `LogFormat` (types.py)

Add `LogFormat = Literal["pretty", "json"]`.

### 2. Add `format` field to `LoggerConfig` (types.py)

New field `format: LogFormat = "pretty"` on the `LoggerConfig` dataclass.

### 3. Config parsing (config.py)

- New `parse_log_format()`: reads `LOG_FORMAT_SERVER`, validates against `"pretty"` / `"json"`, defaults to `"pretty"`, warns on invalid values.
- Rename env var from `LOG_TRANSPORT` to `LOG_TRANSPORT_SERVER`.
- Wire both into `create_default_config()`.

### 4. ConsoleTransport format-aware output (transports/console.py)

- Constructor accepts `format: LogFormat = "pretty"`.
- `format == "json"`: `print(json.dumps(entry))` -- single-line raw StructuredLog to stdout.
- `format == "pretty"`: existing behavior, unchanged.

### 5. Wire format through transport creation (config.py)

- `create_transport()` accepts and passes `format` to `ConsoleTransport`.
- `LOG_FORMAT_SERVER` only affects console transport (Datadog already sends JSON via HTTP).

### 6. Update tests

- All `LOG_TRANSPORT` env var references become `LOG_TRANSPORT_SERVER`.
- New tests for `parse_log_format()` (valid values, invalid fallback, case-insensitive).
- New tests for ConsoleTransport JSON mode (single-line valid JSON, all fields present, routes to stdout).

### 7. Update .env.example and exports

Add `LOG_FORMAT_SERVER` documentation and update `LOG_TRANSPORT` references.

## JSON output example

```json
{"timestamp": "2026-02-22T10:30:00.000Z", "level": "INFO", "category": "DATABASE", "operation": "query", "message": "Running query", "environment": "server", "data": {"table": "users"}}
```
