import os
import sys
import tempfile

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cove_douban_mcp.mcp.transport import stdio_environment


def test_stdio_environment_is_unbuffered_and_does_not_include_secrets(tmp_path) -> None:
    environment = stdio_environment(
        data_root=tmp_path,
        base={"PATH": os.environ.get("PATH", "")},
    )

    assert environment["PYTHONUNBUFFERED"] == "1"
    assert environment["COVE_DOUBAN_DATA_ROOT"] == str(tmp_path)
    assert all("TOKEN" not in key and "COOKIE" not in key for key in environment)


@pytest.mark.asyncio
async def test_installed_stdio_server_initializes_with_official_client(tmp_path) -> None:
    environment = stdio_environment(
        data_root=tmp_path / "data",
        base=os.environ,
    )
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "cove_douban_mcp",
            "serve",
            "--transport",
            "stdio",
        ],
        env=environment,
    )
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
        async with (
            stdio_client(parameters, errlog=stderr) as (reader, writer),
            ClientSession(reader, writer) as session,
        ):
            await session.initialize()
            tools = await session.list_tools()
            status = await session.call_tool("douban_status", {})
        stderr.seek(0)
        error_output = stderr.read()

    assert len(tools.tools) == 12
    assert status.structuredContent["ok"] is True
    assert "Traceback" not in error_output
