"""Read-only access to a fixed allowlist of public Douban charts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import (
    ChartItem,
    SourceFreshness,
    ToolEnvelope,
)
from cove_douban_mcp.services.common import Gateway, gateway_error, warning_from
from cove_douban_mcp.storage.query_cache import QueryCache
from cove_douban_mcp.storage.working_cache import WorkingCache


@dataclass(frozen=True, slots=True)
class ChartSpec:
    board: str
    category: str
    maximum: int


CHART_SPECS: Mapping[str, ChartSpec] = MappingProxyType(
    {
        "movie_weekly": ChartSpec("豆瓣电影一周口碑榜", "movie", 10),
        "movie_north_america": ChartSpec("豆瓣电影北美票房榜", "movie", 10),
        "movie_new": ChartSpec("豆瓣电影新片榜", "movie", 40),
        "movie_top250": ChartSpec("豆瓣电影 Top250", "movie", 250),
        "book_hot": ChartSpec("豆瓣热门图书榜", "book", 50),
        "music_hot": ChartSpec("豆瓣热门音乐榜", "music", 50),
    }
)


class ChartsService:
    def __init__(
        self,
        gateway: Gateway,
        query_cache: QueryCache,
        working_cache: WorkingCache,
    ) -> None:
        self.gateway = gateway
        self.query_cache = query_cache
        self.working_cache = working_cache

    async def get(
        self,
        board: str,
        *,
        limit: int = 10,
        refresh: bool = False,
        scope: str = "default",
    ) -> ToolEnvelope:
        spec = CHART_SPECS.get(board)
        if spec is None:
            raise DoubanError(
                "invalid_argument",
                "board must be one of the six documented chart keys",
            )
        if not 1 <= limit <= spec.maximum:
            raise DoubanError(
                "invalid_argument",
                f"limit must be 1..{spec.maximum} for {board}",
            )

        key = QueryCache.make_key("chart", {"board": board, "limit": limit})
        cached = self.query_cache.get(key)
        source = "query_cache"
        freshness = SourceFreshness(stale=False)
        warning = None

        if cached is None or refresh:
            response = await self.gateway.run(
                "chart",
                [board, "--limit", str(limit)],
            )
            if not response.ok:
                if cached is None:
                    raise gateway_error(response)
                freshness = SourceFreshness(stale=True)
                warning = warning_from(response)
            else:
                items = [
                    ChartItem.model_validate(row).model_dump(mode="json")
                    for row in response.rows[:limit]
                ]
                if not items:
                    raise DoubanError("empty_result", "the selected chart returned no items")
                cached = items
                self.query_cache.put(key, cached)
                source = "live"

        normalized = [ChartItem.model_validate(row).model_dump(mode="json") for row in cached]
        result_ref = self.working_cache.put(
            scope,
            normalized,
            {"operation": "chart", "board": board},
        )
        return ToolEnvelope(
            data={
                "board_key": board,
                "board": spec.board,
                "category": spec.category,
                "items": normalized,
            },
            source=source,
            freshness=freshness,
            result_ref=result_ref,
            warning=warning,
        )
