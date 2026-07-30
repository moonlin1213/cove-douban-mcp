from pathlib import Path

import pytest

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.opencli.gateway import OpenCLIGateway


@pytest.fixture
def fake_opencli() -> Path:
    return Path(__file__).parents[1] / "fixtures" / "fake_opencli.py"


@pytest.mark.asyncio
async def test_gateway_rejects_non_allowlisted_command(fake_opencli) -> None:
    gateway = OpenCLIGateway(fake_opencli)

    with pytest.raises(DoubanError, match="invalid_argument"):
        await gateway.run("download", ["--output", "outside"])


@pytest.mark.asyncio
async def test_gateway_parses_json_without_shell(fake_opencli, tmp_path) -> None:
    gateway = OpenCLIGateway(fake_opencli)
    query = f"示例; touch {tmp_path / 'must-not-exist'}"

    result = await gateway.run("search", [query, "--type", "movie"])

    assert result.rows[0]["title"] == query
    assert not (tmp_path / "must-not-exist").exists()


@pytest.mark.asyncio
async def test_gateway_redacts_sensitive_stderr(fake_opencli) -> None:
    gateway = OpenCLIGateway(fake_opencli)

    result = await gateway.run("search", ["sensitive-error"])

    assert result.ok is False
    assert "private-cookie-value" not in result.safe_error
    assert "private-token-value" not in result.safe_error


@pytest.mark.asyncio
async def test_gateway_maps_timeout(fake_opencli) -> None:
    gateway = OpenCLIGateway(fake_opencli, timeout_seconds=0.01)

    with pytest.raises(DoubanError, match="source_timeout"):
        await gateway.run("search", ["timeout"])

