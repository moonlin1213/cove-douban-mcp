"""Normalized Douban list metadata and items."""

from __future__ import annotations

import re
from typing import Literal

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import Doulist, DoulistItem, SourceFreshness, ToolEnvelope
from cove_douban_mcp.services.common import Gateway, gateway_error
from cove_douban_mcp.storage.query_cache import QueryCache
from cove_douban_mcp.storage.working_cache import WorkingCache

_DOULIST_ID = re.compile(r"(?:^|/)(\d+)(?:/|$)")


class DoulistsService:
    def __init__(
        self,
        gateway: Gateway,
        query_cache: QueryCache,
        working_cache: WorkingCache,
    ) -> None:
        self.gateway = gateway
        self.query_cache = query_cache
        self.working_cache = working_cache

    async def list_doulists(
        self,
        *,
        kind: Literal["all", "movie", "book"] = "all",
        limit: int = 30,
        uid: str = "",
        refresh: bool = False,
        scope: str = "default",
    ) -> ToolEnvelope:
        if not 1 <= limit <= 80:
            raise DoubanError("invalid_argument", "limit must be 1..80")
        parameters = {"kind": kind, "limit": limit, "uid": uid.strip()}
        key = QueryCache.make_key("doulists", parameters)
        cached = None if refresh else self.query_cache.get(key)
        source = "query_cache"
        if cached is None:
            arguments = ["--kind", kind, "--limit", str(limit)]
            if uid.strip():
                arguments.extend(["--uid", uid.strip()])
            response = await self.gateway.run("doulists", arguments)
            if not response.ok:
                raise gateway_error(response)
            cached = [
                Doulist.model_validate(row).model_dump(mode="json")
                for row in response.rows[:limit]
            ]
            self.query_cache.put(key, cached)
            source = "live"
        items = [Doulist.model_validate(row).model_dump(mode="json") for row in cached]
        result_ref = self.working_cache.put(
            scope,
            items,
            {"operation": "doulists", "kind": kind},
        )
        return ToolEnvelope(
            data={"items": items},
            source=source,
            freshness=SourceFreshness(stale=False),
            result_ref=result_ref,
        )

    async def list_items(
        self,
        doulist_id: str,
        *,
        limit: int = 40,
        refresh: bool = False,
        scope: str = "default",
    ) -> ToolEnvelope:
        if not 1 <= limit <= 120:
            raise DoubanError("invalid_argument", "limit must be 1..120")
        match = _DOULIST_ID.search(doulist_id.strip())
        if match is None:
            raise DoubanError("invalid_argument", "doulist id must contain a numeric id")
        normalized_id = match.group(1)
        key = QueryCache.make_key("doulist", {"id": normalized_id, "limit": limit})
        cached = None if refresh else self.query_cache.get(key)
        source = "query_cache"
        if cached is None:
            response = await self.gateway.run(
                "doulist",
                [normalized_id, "--limit", str(limit)],
            )
            if not response.ok:
                raise gateway_error(response)
            cached = [
                DoulistItem.model_validate(row).model_dump(mode="json")
                for row in response.rows[:limit]
            ]
            self.query_cache.put(key, cached)
            source = "live"
        items = [DoulistItem.model_validate(row).model_dump(mode="json") for row in cached]
        result_ref = self.working_cache.put(
            scope,
            items,
            {"operation": "doulist_items", "doulist_id": normalized_id},
        )
        return ToolEnvelope(
            data={"items": items},
            source=source,
            freshness=SourceFreshness(stale=False),
            result_ref=result_ref,
        )

