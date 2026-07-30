"""Public catalog search and subject lookup."""

from __future__ import annotations

import re
from typing import Literal

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import SearchResult, SourceFreshness, Subject, ToolEnvelope
from cove_douban_mcp.services.common import Gateway, gateway_error
from cove_douban_mcp.storage.query_cache import QueryCache
from cove_douban_mcp.storage.working_cache import WorkingCache

_SUBJECT_ID = re.compile(r"(?:^|/)(\d+)(?:/|$)")


class CatalogService:
    def __init__(
        self,
        gateway: Gateway,
        query_cache: QueryCache,
        working_cache: WorkingCache,
    ) -> None:
        self.gateway = gateway
        self.query_cache = query_cache
        self.working_cache = working_cache

    async def search(
        self,
        query: str,
        *,
        media_type: Literal["movie", "book", "music"] = "movie",
        limit: int = 5,
        refresh: bool = False,
        scope: str = "default",
    ) -> ToolEnvelope:
        if not query.strip() or not 1 <= limit <= 10:
            raise DoubanError("invalid_argument", "query is required and limit must be 1..10")
        parameters = {"query": query.strip(), "type": media_type, "limit": limit}
        key = QueryCache.make_key("search", parameters)
        cached = None if refresh else self.query_cache.get(key)
        source = "query_cache"
        if cached is None:
            response = await self.gateway.run(
                "search",
                [query.strip(), "--type", media_type, "--limit", str(limit)],
            )
            if not response.ok:
                raise gateway_error(response)
            models = [SearchResult.model_validate(row) for row in response.rows[:limit]]
            cached = [model.model_dump(mode="json") for model in models]
            self.query_cache.put(key, cached)
            source = "live"
        items = [SearchResult.model_validate(row).model_dump(mode="json") for row in cached]
        result_ref = self.working_cache.put(
            scope,
            items,
            {"operation": "search", "media_type": media_type},
        )
        return ToolEnvelope(
            data={"items": items},
            source=source,
            freshness=SourceFreshness(stale=False),
            result_ref=result_ref,
        )

    async def subject(
        self,
        subject_id: str,
        *,
        media_type: Literal["movie", "book"] = "movie",
        refresh: bool = False,
    ) -> ToolEnvelope:
        match = _SUBJECT_ID.search(subject_id.strip())
        if match is None:
            raise DoubanError("invalid_argument", "subject id must contain a numeric id")
        normalized_id = match.group(1)
        key = QueryCache.make_key(
            "subject",
            {"id": normalized_id, "type": media_type},
        )
        cached = None if refresh else self.query_cache.get(key)
        source = "query_cache"
        if cached is None:
            response = await self.gateway.run(
                "subject",
                [normalized_id, "--type", media_type],
            )
            if not response.ok:
                raise gateway_error(response)
            if not response.rows:
                raise DoubanError("empty_result", "no matching subject was found")
            cached = Subject.model_validate(response.rows[0]).model_dump(mode="json")
            self.query_cache.put(key, cached)
            source = "live"
        subject = Subject.model_validate(cached).model_dump(mode="json")
        return ToolEnvelope(
            data={"subject": subject},
            source=source,
            freshness=SourceFreshness(stale=False),
        )

