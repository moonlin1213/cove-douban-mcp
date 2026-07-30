import pytest

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.opencli.parser import parse_opencli_json, redact_diagnostic


def test_parser_accepts_rows_envelope_and_plain_array() -> None:
    assert parse_opencli_json('{"rows":[{"id":"1"}]}') == [{"id": "1"}]
    assert parse_opencli_json('[{"id":"2"}]') == [{"id": "2"}]


def test_parser_rejects_malformed_and_non_row_results() -> None:
    with pytest.raises(DoubanError, match="source_malformed"):
        parse_opencli_json("not-json")
    with pytest.raises(DoubanError, match="source_malformed"):
        parse_opencli_json('{"rows":["not-an-object"]}')


def test_parser_maps_typed_adapter_error() -> None:
    with pytest.raises(DoubanError, match="login_required"):
        parse_opencli_json('{"error":{"code":"login_required","message":"Sign in"}}')


def test_diagnostics_are_redacted_without_echoing_secrets() -> None:
    redacted = redact_diagnostic(
        "Cookie: private-cookie-value Authorization: Bearer private-token-value"
    )

    assert "private-cookie-value" not in redacted
    assert "private-token-value" not in redacted
    assert "[redacted]" in redacted

