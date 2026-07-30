"""Normalized review reads."""

from __future__ import annotations

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import Review, SourceFreshness, ToolEnvelope
from cove_douban_mcp.services.common import Gateway, gateway_error
from cove_douban_mcp.storage.query_cache import QueryCache
from cove_douban_mcp.storage.working_cache import WorkingCache


class ReviewsService:
    def __init__(
        self,
        gateway: Gateway,
        query_cache: QueryCache,
        working_cache: WorkingCache,
    ) -> None:
        self.gateway = gateway
        self.query_cache = query_cache
        self.working_cache = working_cache

    async def list_reviews(
        self,
        *,
        limit: int = 20,
        uid: str = "",
        full: bool = False,
        refresh: bool = False,
        scope: str = "default",
    ) -> ToolEnvelope:
        if not 1 <= limit <= 50:
            raise DoubanError("invalid_argument", "limit must be 1..50")
        parameters = {"limit": limit, "uid": uid.strip(), "full": full}
        key = QueryCache.make_key("reviews", parameters)
        cached = None if refresh else self.query_cache.get(key)
        source = "query_cache"
        if cached is None:
            arguments = ["--limit", str(limit), "--full", str(full).lower()]
            if uid.strip():
                arguments.extend(["--uid", uid.strip()])
            response = await self.gateway.run("reviews", arguments)
            if not response.ok:
                raise gateway_error(response)
            cached = [
                Review.model_validate(row).model_dump(mode="json")
                for row in response.rows[:limit]
            ]
            self.query_cache.put(key, cached)
            source = "live"
        items = [Review.model_validate(row).model_dump(mode="json") for row in cached]
        result_ref = self.working_cache.put(
            scope,
            items,
            {"operation": "reviews", "full": full},
        )
        return ToolEnvelope(
            data={"items": items},
            source=source,
            freshness=SourceFreshness(stale=False),
            result_ref=result_ref,
        )

