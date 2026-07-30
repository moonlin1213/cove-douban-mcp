from datetime import timedelta

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from cove_douban_mcp.mcp.server import create_mcp_server

EXPECTED_TOOLS = {
    "douban_status",
    "douban_search",
    "douban_subject",
    "douban_movie_marks",
    "douban_reviews",
    "douban_movie_profile",
    "douban_doulists",
    "douban_doulist_items",
    "douban_sync",
    "douban_working_cache_read",
    "douban_export_markdown",
}


@pytest.mark.asyncio
async def test_server_exposes_exact_v010_tool_surface(container) -> None:
    server = create_mcp_server(container)

    async with create_connected_server_and_client_session(
        server,
        read_timeout_seconds=timedelta(seconds=5),
    ) as session:
        result = await session.list_tools()

    assert {tool.name for tool in result.tools} == EXPECTED_TOOLS


@pytest.mark.asyncio
async def test_tool_returns_structured_error_instead_of_traceback(container) -> None:
    server = create_mcp_server(container)

    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool(
            "douban_subject",
            {"id": "not-a-subject", "type": "movie"},
        )

    assert result.isError is False
    assert result.structuredContent["ok"] is False
    assert result.structuredContent["error"]["code"] == "invalid_argument"

