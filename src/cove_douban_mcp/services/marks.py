"""Cache-first movie marks and compact profile service."""

from __future__ import annotations

from typing import Literal

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.filters import MarkFilters, filter_movie_marks
from cove_douban_mcp.domain.models import MovieMark, SourceFreshness, ToolEnvelope, ToolError
from cove_douban_mcp.domain.pagination import paginate
from cove_douban_mcp.services.common import Gateway, gateway_error, warning_from
from cove_douban_mcp.storage.marks_store import MarksStore
from cove_douban_mcp.storage.query_cache import QueryCache
from cove_douban_mcp.storage.working_cache import WorkingCache

MarkStatus = Literal["wish", "collect", "do"]


class MarksService:
    def __init__(
        self,
        gateway: Gateway,
        marks_store: MarksStore,
        query_cache: QueryCache,
        working_cache: WorkingCache,
    ) -> None:
        self.gateway = gateway
        self.marks_store = marks_store
        self.query_cache = query_cache
        self.working_cache = working_cache

    async def _status_items(
        self,
        status: MarkStatus,
        *,
        uid: str,
        refresh: bool,
    ) -> tuple[list[MovieMark], str, bool, ToolError | None]:
        if uid:
            key = QueryCache.make_key("marks-full", {"status": status, "uid": uid})
            cached = self.query_cache.get(key)
            if cached is not None and not refresh:
                return (
                    [MovieMark.model_validate(row) for row in cached],
                    "query_cache",
                    False,
                    None,
                )
            arguments = ["--status", status, "--uid", uid]
            response = await self.gateway.run("marks-full", arguments)
            if not response.ok:
                if cached is not None:
                    return (
                        [MovieMark.model_validate(row) for row in cached],
                        "query_cache",
                        True,
                        warning_from(response),
                    )
                raise gateway_error(response)
            items = [MovieMark.model_validate(row) for row in response.rows]
            self.query_cache.put(
                key,
                [item.model_dump(mode="json") for item in items],
            )
            return items, "live", False, None

        baseline = self.marks_store.load().statuses.get(status, [])
        if baseline and not refresh:
            return baseline, "full_cache", False, None
        response = await self.gateway.run("marks-full", ["--status", status])
        if not response.ok:
            if baseline:
                return baseline, "full_cache", True, warning_from(response)
            raise gateway_error(response)
        items = [MovieMark.model_validate(row) for row in response.rows]
        saved = self.marks_store.merge_status(status, items)
        return saved.statuses.get(status, []), "live", False, None

    async def list_marks(
        self,
        *,
        status: Literal["wish", "collect", "do", "all"] = "collect",
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
        scope: str = "default",
    ) -> ToolEnvelope:
        statuses: list[MarkStatus] = (
            ["wish", "collect", "do"] if status == "all" else [status]
        )
        combined: list[MovieMark] = []
        sources: list[str] = []
        stale = False
        warning: ToolError | None = None
        for selected in statuses:
            items, source, was_stale, item_warning = await self._status_items(
                selected,
                uid=uid.strip(),
                refresh=refresh,
            )
            combined.extend(items)
            sources.append(source)
            stale = stale or was_stale
            warning = warning or item_warning

        filtered = filter_movie_marks(
            combined,
            MarkFilters(
                query=query,
                genre=genre,
                country=country,
                director=director,
                cast=cast,
                year_from=year_from,
                year_to=year_to,
                exclude=exclude,
            ),
        )
        serialized = [item.model_dump(mode="json") for item in filtered]
        result_ref = self.working_cache.put(
            scope,
            serialized,
            {"operation": "movie_marks", "status": status},
        )
        page, pagination = paginate(serialized, offset=offset, limit=limit)
        return ToolEnvelope(
            data={"items": page},
            source=sources[0] if len(set(sources)) == 1 else "mixed",
            freshness=SourceFreshness(stale=stale),
            warning=warning,
            pagination=pagination,
            result_ref=result_ref,
        )

    async def profile(
        self,
        *,
        statuses: list[MarkStatus] | None = None,
        limit_per_status: int = 20,
        refresh: bool = False,
        scope: str = "default",
    ) -> ToolEnvelope:
        if not 1 <= limit_per_status <= 80:
            raise DoubanError("invalid_argument", "limit_per_status must be 1..80")
        requested = statuses or ["wish", "collect", "do"]
        sections: dict[str, object] = {}
        stale = False
        for status in requested:
            result = await self.list_marks(
                status=status,
                limit=limit_per_status,
                refresh=refresh,
                scope=scope,
            )
            sections[status] = result.data
            stale = stale or bool(result.freshness and result.freshness.stale)
        return ToolEnvelope(
            data={"sections": sections},
            source="profile",
            freshness=SourceFreshness(stale=stale),
        )

