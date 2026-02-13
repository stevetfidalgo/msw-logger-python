"""Tests for DatadogTransport."""

from unittest.mock import MagicMock, patch

from msw_logger.transports.datadog import DatadogTransport
from msw_logger.types import DatadogConfig, StructuredLog


def _make_log(level: str = "INFO") -> StructuredLog:
    return {
        "timestamp": "2025-01-15T10:30:00.000Z",
        "level": level,
        "category": "TEST",
        "operation": "test-op",
        "message": "Test message",
        "environment": "server",
    }


class TestDatadogTransport:
    def test_name_is_datadog(self):
        config = DatadogConfig(api_key="test-key")
        transport = DatadogTransport(config)
        assert transport.name == "datadog"

    def test_log_sends_http_request(self):
        config = DatadogConfig(api_key="test-key", site="datadoghq.com")
        transport = DatadogTransport(config)
        mock_response = MagicMock()
        mock_response.status = 202
        mock_response.read.return_value = b""
        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            transport.log(_make_log("INFO"))
        mock_urlopen.assert_called_once()
        # Verify the request object
        request = mock_urlopen.call_args[0][0]
        assert "datadoghq.com" in request.full_url
        assert request.get_header("Dd-api-key") == "test-key"
        assert request.get_header("Content-type") == "application/json"

    def test_log_does_not_raise_on_http_error(self):
        config = DatadogConfig(api_key="test-key")
        transport = DatadogTransport(config)
        with patch("urllib.request.urlopen", side_effect=Exception("network error")):
            # Should not raise
            transport.log(_make_log("ERROR"))

    def test_maps_log_levels(self):
        config = DatadogConfig(api_key="test-key")
        transport = DatadogTransport(config)
        mock_response = MagicMock()
        mock_response.status = 202
        mock_response.read.return_value = b""

        import json
        for level, expected_dd_status in [
            ("TRACE", "debug"),
            ("DEBUG", "debug"),
            ("INFO", "info"),
            ("WARN", "warn"),
            ("ERROR", "error"),
        ]:
            with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
                transport.log(_make_log(level))
            request = mock_urlopen.call_args[0][0]
            payload = json.loads(request.data)
            assert payload[0]["status"] == expected_dd_status
