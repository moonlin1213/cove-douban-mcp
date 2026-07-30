import pytest
from starlette.testclient import TestClient

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.mcp.auth import LocalBearerAuth, load_or_create_http_token
from cove_douban_mcp.mcp.server import create_mcp_server
from cove_douban_mcp.mcp.transport import build_http_app, validate_loopback_host


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.2", "example.invalid"])
def test_non_loopback_host_is_rejected(host) -> None:
    with pytest.raises(DoubanError, match="unsafe_http_host"):
        validate_loopback_host(host)


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_loopback_host_is_accepted(host) -> None:
    assert validate_loopback_host(host) == host


def test_local_http_rejects_missing_token_and_bad_origin(container) -> None:
    server = create_mcp_server(container)
    app = build_http_app(
        server,
        auth=LocalBearerAuth(
            token="test-only-token-with-at-least-256-bits-of-space",
            allowed_origins={"http://127.0.0.1:3000"},
        ),
    )

    with TestClient(app) as client:
        missing = client.get("/mcp")
        wrong_origin = client.get(
            "/mcp",
            headers={
                "Authorization": (
                    "Bearer test-only-token-with-at-least-256-bits-of-space"
                ),
                "Origin": "https://untrusted.example",
            },
        )
        accepted_by_auth = client.get(
            "/mcp",
            headers={
                "Authorization": (
                    "Bearer test-only-token-with-at-least-256-bits-of-space"
                ),
                "Origin": "http://127.0.0.1:3000",
            },
        )

    assert missing.status_code == 401
    assert wrong_origin.status_code == 403
    assert accepted_by_auth.status_code not in {401, 403}


def test_http_auth_rejects_short_configured_secret() -> None:
    with pytest.raises(ValueError, match="256"):
        LocalBearerAuth(token="too-short")


def test_generated_http_token_is_private_and_stable(tmp_path) -> None:
    path = tmp_path / "http-token"

    first = load_or_create_http_token(path)
    second = load_or_create_http_token(path)

    assert first == second
    assert len(first) >= 43
    assert path.stat().st_mode & 0o077 == 0
