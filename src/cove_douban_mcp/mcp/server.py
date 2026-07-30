"""FastMCP server construction."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from cove_douban_mcp.mcp.tools import register_tools
from cove_douban_mcp.services.container import ServiceContainer


def create_mcp_server(container: ServiceContainer) -> FastMCP:
    server = FastMCP(
        "cove-douban-mcp",
        instructions=(
            "Read-only Douban access through the user's local browser session. "
            "Markdown export is separate, optional, and disabled by default."
        ),
        json_response=True,
        stateless_http=False,
        streamable_http_path="/mcp",
    )
    register_tools(server, container)
    return server

