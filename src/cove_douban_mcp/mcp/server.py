"""FastMCP server construction."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any

from mcp.server.fastmcp import FastMCP

from cove_douban_mcp.mcp.tools import register_tools
from cove_douban_mcp.services.container import ServiceContainer
from cove_douban_mcp.services.scheduler import SyncScheduler


def create_mcp_server(container: ServiceContainer) -> FastMCP:
    scheduler = SyncScheduler(
        sync_service=container.sync,
        settings=container.settings.sync,
        state_store=container.sync_state_store,
    )

    @asynccontextmanager
    async def lifespan(_server: FastMCP[Any]) -> AsyncIterator[dict[str, Any]]:
        task = asyncio.create_task(scheduler.run(), name="cove-douban-daily-sync")
        try:
            yield {}
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    server = FastMCP(
        "cove-douban-mcp",
        instructions=(
            "Read-only Douban access through the user's local browser session. "
            "Markdown export is separate, optional, and disabled by default."
        ),
        json_response=True,
        stateless_http=False,
        streamable_http_path="/mcp",
        lifespan=lifespan,
    )
    register_tools(server, container)
    return server
