"""Safe reads from opaque server-side working results."""

from __future__ import annotations

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import ToolEnvelope
from cove_douban_mcp.storage.working_cache import WorkingCache


class WorkingResultService:
    def __init__(self, cache: WorkingCache) -> None:
        self.cache = cache

    async def read(
        self,
        *,
        scope: str,
        result_ref: str,
        page: int = 0,
        page_size: int = 30,
    ) -> ToolEnvelope:
        if page < 0:
            raise DoubanError("invalid_argument", "page must be zero or greater")
        working_page = self.cache.read(
            scope,
            result_ref,
            page=max(1, page),
            page_size=page_size,
        )
        if page == 0:
            data = {
                "metadata": working_page.metadata,
                "total": working_page.pagination.total,
            }
        else:
            data = {
                "metadata": working_page.metadata,
                "items": working_page.items,
            }
        return ToolEnvelope(
            data=data,
            source="working_cache",
            pagination=working_page.pagination if page > 0 else None,
            result_ref=result_ref,
        )

