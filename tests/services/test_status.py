import pytest


@pytest.mark.asyncio
async def test_status_reports_permissions_without_exposing_paths(container) -> None:
    result = await container.status.status()

    assert result.ok is True
    assert result.data["douban_access"] == "read_only"
    assert result.data["export"]["enabled"] is False
    assert "root" not in result.data["export"]
