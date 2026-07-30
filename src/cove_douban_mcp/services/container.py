"""Construction root for all application services."""

from __future__ import annotations

from dataclasses import dataclass

from cove_douban_mcp.config import Settings
from cove_douban_mcp.services.catalog import CatalogService
from cove_douban_mcp.services.common import Gateway
from cove_douban_mcp.services.doulists import DoulistsService
from cove_douban_mcp.services.marks import MarksService
from cove_douban_mcp.services.reviews import ReviewsService
from cove_douban_mcp.services.status import StatusService
from cove_douban_mcp.services.sync import SyncService
from cove_douban_mcp.storage.marks_store import MarksStore
from cove_douban_mcp.storage.paths import AppPaths
from cove_douban_mcp.storage.query_cache import QueryCache
from cove_douban_mcp.storage.sync_state import SyncStateStore
from cove_douban_mcp.storage.working_cache import WorkingCache


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    paths: AppPaths
    gateway: Gateway
    query_cache: QueryCache
    marks_store: MarksStore
    sync_state_store: SyncStateStore
    working_cache: WorkingCache
    catalog: CatalogService
    marks: MarksService
    reviews: ReviewsService
    doulists: DoulistsService
    sync: SyncService
    status: StatusService

    @classmethod
    def create(
        cls,
        *,
        settings: Settings,
        paths: AppPaths,
        gateway: Gateway,
    ) -> ServiceContainer:
        paths.ensure()
        query_cache = QueryCache(
            paths.query_cache,
            ttl_seconds=settings.cache.query_ttl_seconds,
            max_entries=settings.cache.query_max_entries,
        )
        marks_store = MarksStore(paths.marks)
        sync_state_store = SyncStateStore(paths.sync_state)
        working_cache = WorkingCache(
            paths.working,
            ttl_seconds=settings.cache.working_ttl_seconds,
            max_refs_per_scope=settings.cache.working_max_refs_per_scope,
            max_bytes_per_ref=settings.cache.working_max_bytes_per_ref,
            max_total_bytes_per_scope=settings.cache.working_max_total_bytes_per_scope,
        )
        catalog = CatalogService(gateway, query_cache, working_cache)
        marks = MarksService(gateway, marks_store, query_cache, working_cache)
        reviews = ReviewsService(gateway, query_cache, working_cache)
        doulists = DoulistsService(gateway, query_cache, working_cache)
        sync = SyncService(
            marks,
            doulists,
            sync_state_store,
            paths.cache / "sync.lock",
        )
        status = StatusService(settings, marks_store, sync_state_store)
        return cls(
            settings=settings,
            paths=paths,
            gateway=gateway,
            query_cache=query_cache,
            marks_store=marks_store,
            sync_state_store=sync_state_store,
            working_cache=working_cache,
            catalog=catalog,
            marks=marks,
            reviews=reviews,
            doulists=doulists,
            sync=sync,
            status=status,
        )
