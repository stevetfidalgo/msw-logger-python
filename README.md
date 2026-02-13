# msw-logger

Structured logging for Python server applications with Console and Datadog transports.

## Features

- **Zero dependencies** — Core logger uses only the Python standard library
- **Structured logging** — Consistent format for log aggregation
- **Category-specific log levels** — Fine-grained control over logging verbosity
- **Request/connection correlation** — Track related logs across services
- **Automatic data sanitization** — Removes passwords, tokens, and secrets
- **Multiple transports** — Console (ANSI-colored) and Datadog

## Installation

```bash
pip install msw-logger

# With Datadog support (optional)
pip install msw-logger[datadog]
```

## Quick Start

```python
from msw_logger import logger, LogCat

# Simple info log
logger.info(LogCat.STARTUP, "init", "Application started")

# Log with structured data
logger.info(LogCat.DATABASE, "query", "Running query", {
    "table": "users",
    "limit": 10,
})

# Error logging
try:
    risky_operation()
except Exception as e:
    logger.error(LogCat.SERVICE, "operation_failed", "Operation failed", e)

# Debug logging (filtered based on LOG_LEVEL)
logger.debug(LogCat.CACHE, "hit", "Cache hit", {"key": "user:123"})
```

## API Signature

```python
logger.trace(category, operation, message, data=None)
logger.debug(category, operation, message, data=None)
logger.info(category, operation, message, data=None)
logger.warn(category, operation, message, data=None)
logger.error(category, operation, message, data_or_error=None)
```

**Parameters:**
- `category` — Classification using `LogCat` constants or any string
- `operation` — Specific operation being logged (e.g., `"query"`, `"login"`)
- `message` — Human-readable description
- `data` — Optional dict of structured data, or an `Exception` for `error()`

## Configuration

### Environment Variables

```bash
# General Logging Configuration
LOG_LEVEL=INFO                          # TRACE, DEBUG, INFO, WARN, ERROR
LOG_TRANSPORT=console                   # console, datadog

# Category-Specific Log Levels (optional)
LOG_CATEGORY_LEVELS=DATABASE:DEBUG,AUTH:TRACE,HTTP:WARN

# Datadog Configuration (if LOG_TRANSPORT=datadog)
DATADOG_API_KEY=your_api_key_here
DATADOG_SERVICE_NAME=my-app
DATADOG_ENV=development
DATADOG_SITE=datadoghq.com
```

### Log Levels

Log levels in order of severity (lowest to highest):

1. **TRACE** — Very detailed diagnostic information
2. **DEBUG** — Detailed diagnostic information
3. **INFO** — General informational messages
4. **WARN** — Warning messages for potentially harmful situations
5. **ERROR** — Error events

Only logs at or above the configured `LOG_LEVEL` are output.

### Category-Specific Log Levels

Override the default level for specific categories:

```bash
LOG_LEVEL=INFO
LOG_CATEGORY_LEVELS=DATABASE:DEBUG,AUTH:TRACE,HTTP:WARN
```

Programmatic configuration:

```python
from msw_logger import create_logger, LogLevel

logger = create_logger(
    level=LogLevel.INFO,
    category_levels={
        "DATABASE": LogLevel.DEBUG,
        "AUTH": LogLevel.TRACE,
        "HTTP": LogLevel.WARN,
    },
)
```

## Log Categories

Built-in categories via `LogCat`:

| Category | Description |
|----------|-------------|
| `HTTP_REQUEST` / `HTTP_RESPONSE` | HTTP traffic |
| `DATABASE` / `MIGRATION` | Database operations |
| `AUTH` / `SECURITY` | Authentication and security |
| `SERVICE` / `WORKFLOW` | Business logic |
| `EXTERNAL_API` / `API_CALL` | External service calls |
| `JOB` / `CRON` | Background and scheduled tasks |
| `CACHE` / `FILE_SYSTEM` | Storage operations |
| `STARTUP` / `SHUTDOWN` / `HEALTH` | Lifecycle |
| `EMAIL` / `SMS` | Notifications |
| `MIDDLEWARE` / `VALIDATION` / `WEBSOCKET` | Infrastructure |

Define custom categories for your domain:

```python
class MyLogCat:
    PAYMENT = "PAYMENT"
    CART = "CART"
    ORDER = "ORDER"

logger.info(MyLogCat.PAYMENT, "charge", "Processing payment", {"amount": 99.99})
```

## Advanced Usage

### Request ID Correlation

```python
from msw_logger import logger, generate_request_id

request_id = generate_request_id()
logger.set_request_id(request_id)

logger.info("API", "handle", "Processing request")
# Log output includes request_id for correlation

logger.clear_request_id()
```

### Child Loggers

Create scoped loggers with preset context:

```python
request_logger = logger.child(request_id="req-123", module="api-handler")
request_logger.info("API", "process", "Handling request")
# Automatically includes request_id and module
```

### Custom Logger Instance

```python
from msw_logger import create_logger, ConsoleTransport, LogLevel

custom_logger = create_logger(
    level=LogLevel.DEBUG,
    transports=[ConsoleTransport()],
    include_stack_traces=True,
    max_data_depth=10,
)
```

## Console Output

```
[2026-01-15T10:30:00.000Z] INFO [DATABASE] query
  Message: Running query
  Data:
    {
      "table": "users",
      "limit": 10
    }
  Request ID: 550e8400-e29b-41d4-a716-446655440000
```

## Development

```bash
# Create environment
mamba env create -f environment.yml

# Activate environment
mamba activate msw-logger-python

# Run tests
pytest -v

# Lint
ruff check src/ tests/
```

## License

MIT
