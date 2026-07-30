from pathlib import Path

import pytest

from cove_douban_mcp.opencli.diagnostics import OpenCLIDiagnostics


@pytest.mark.asyncio
async def test_diagnostics_reports_synthetic_binary_version() -> None:
    binary = Path(__file__).parents[1] / "fixtures" / "fake_opencli.py"

    result = await OpenCLIDiagnostics(binary).check()

    assert result.available is True
    assert result.version == "1.8.6"
