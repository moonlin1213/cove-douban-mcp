"""The exact public v0.1.0 MCP tool catalog."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, Literal

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import ToolEnvelope, ToolError
from cove_douban_mcp.services.container import ServiceContainer

MCPContext = Context[Any, Any, Any]


def _scope(context: MCPContext) -> str:
    return str(context.client_id or context.request_id or "local-client")


async def _safe(call: Awaitable[BaseModel]) -> dict[str, Any]:
    try:
        result = await call
    except DoubanError as error:
        return ToolEnvelope(
            ok=False,
            error=ToolError(
                code=error.code,
                message=error.message,
                action=error.action,
            ),
        ).model_dump(mode="json", exclude_none=True)
    except Exception:
        return ToolEnvelope(
            ok=False,
            error=ToolError(
                code="internal_error",
                message="the local MCP operation failed safely",
                action="Run the doctor command and inspect local redacted logs.",
            ),
        ).model_dump(mode="json", exclude_none=True)
    return result.model_dump(mode="json", exclude_none=True)


def register_tools(server: FastMCP, container: ServiceContainer) -> None:
    @server.tool(name="douban_status")
    async def douban_status() -> dict[str, Any]:
        """Report safe local readiness, permissions, caches, and sync status."""

        return await _safe(container.status.status())

    @server.tool(name="douban_search")
    async def douban_search(
        query: str,
        type: Literal["movie", "book", "music"] = "movie",
        limit: int = 5,
        refresh: bool = False,
        ctx: MCPContext | None = None,
    ) -> dict[str, Any]:
        """Search read-only Douban subjects."""

        scope = _scope(ctx) if ctx else "local-client"
        return await _safe(
            container.catalog.search(
                query,
                media_type=type,
                limit=limit,
                refresh=refresh,
                scope=scope,
            )
        )

    @server.tool(name="douban_subject")
    async def douban_subject(
        id: str,
        type: Literal["movie", "book"] = "movie",
        refresh: bool = False,
    ) -> dict[str, Any]:
        """Read one normalized movie or book subject."""

        return await _safe(
            container.catalog.subject(id, media_type=type, refresh=refresh)
        )

    @server.tool(name="douban_movie_marks")
    async def douban_movie_marks(
        status: Literal["collect", "wish", "do", "all"] = "collect",
        limit: int = 30,
        offset: int = 0,
        uid: str = "",
        refresh: bool = False,
        query: str = "",
        exclude: str | list[str] = "",
        genre: str = "",
        country: str = "",
        director: str = "",
        cast: str = "",
        year_from: int | None = None,
        year_to: int | None = None,
        ctx: MCPContext | None = None,
    ) -> dict[str, Any]:
        """Read, filter, and page movie marks without modifying Douban."""

        return await _safe(
            container.marks.list_marks(
                status=status,
                limit=limit,
                offset=offset,
                uid=uid,
                refresh=refresh,
                query=query,
                exclude=exclude,
                genre=genre,
                country=country,
                director=director,
                cast=cast,
                year_from=year_from,
                year_to=year_to,
                scope=_scope(ctx) if ctx else "local-client",
            )
        )

    @server.tool(name="douban_reviews")
    async def douban_reviews(
        limit: int = 20,
        uid: str = "",
        full: bool = False,
        refresh: bool = False,
        ctx: MCPContext | None = None,
    ) -> dict[str, Any]:
        """Read normalized reviews visible to the local browser session."""

        return await _safe(
            container.reviews.list_reviews(
                limit=limit,
                uid=uid,
                full=full,
                refresh=refresh,
                scope=_scope(ctx) if ctx else "local-client",
            )
        )

    @server.tool(name="douban_movie_profile")
    async def douban_movie_profile(
        statuses: list[Literal["collect", "wish", "do"]] | None = None,
        limit_per_status: int = 20,
        refresh: bool = False,
        ctx: MCPContext | None = None,
    ) -> dict[str, Any]:
        """Read compact sections across movie-mark statuses."""

        return await _safe(
            container.marks.profile(
                statuses=statuses,
                limit_per_status=limit_per_status,
                refresh=refresh,
                scope=_scope(ctx) if ctx else "local-client",
            )
        )

    @server.tool(name="douban_doulists")
    async def douban_doulists(
        kind: Literal["all", "movie", "book"] = "all",
        limit: int = 30,
        uid: str = "",
        refresh: bool = False,
        ctx: MCPContext | None = None,
    ) -> dict[str, Any]:
        """Read normalized Douban list metadata."""

        return await _safe(
            container.doulists.list_doulists(
                kind=kind,
                limit=limit,
                uid=uid,
                refresh=refresh,
                scope=_scope(ctx) if ctx else "local-client",
            )
        )

    @server.tool(name="douban_doulist_items")
    async def douban_doulist_items(
        id: str,
        limit: int = 40,
        refresh: bool = False,
        ctx: MCPContext | None = None,
    ) -> dict[str, Any]:
        """Read normalized entries from one Douban list."""

        return await _safe(
            container.doulists.list_items(
                id,
                limit=limit,
                refresh=refresh,
                scope=_scope(ctx) if ctx else "local-client",
            )
        )

    @server.tool(name="douban_sync")
    async def douban_sync(
        statuses: list[Literal["collect", "wish", "do"]] | None = None,
        include_doulists: bool = True,
        force: bool = False,
    ) -> dict[str, Any]:
        """Refresh internal read-only caches; never writes to Douban."""

        result = await _safe(
            container.sync.sync(
                statuses=statuses,
                include_doulists=include_doulists,
                force=force,
                reason="manual",
            )
        )
        if "error" in result:
            return result
        return ToolEnvelope(
            ok=bool(result.get("ok")),
            data={"sync": result},
            source="local_sync",
        ).model_dump(mode="json", exclude_none=True)

    @server.tool(name="douban_working_cache_read")
    async def douban_working_cache_read(
        result_ref: str,
        page: int = 0,
        page_size: int = 30,
        ctx: MCPContext | None = None,
    ) -> dict[str, Any]:
        """Page a complete verified result held behind an opaque reference."""

        return await _safe(
            container.working.read(
                scope=_scope(ctx) if ctx else "local-client",
                result_ref=result_ref,
                page=page,
                page_size=page_size,
            )
        )

    @server.tool(name="douban_export_markdown")
    async def douban_export_markdown(
        result_ref: str,
        path: str,
        mode: Literal["create", "append", "replace"] = "create",
        heading: str = "",
        ctx: MCPContext | None = None,
    ) -> dict[str, Any]:
        """Request optional Markdown export within the local user's policy."""

        return await _safe(
            container.export.request(
                scope=_scope(ctx) if ctx else "local-client",
                result_ref=result_ref,
                path=path,
                mode=mode,
                heading=heading,
            )
        )
