"""Small no-LLM scheduler for daily cache refresh and startup catch-up."""

from __future__ import annotations

import asyncio
from datetime import datetime, time
from typing import Literal, cast

from cove_douban_mcp.config import SyncSettings
from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.services.marks import MarkStatus
from cove_douban_mcp.services.sync import SyncService
from cove_douban_mcp.storage.sync_state import SyncStateStore


class SyncScheduler:
    def __init__(
        self,
        *,
        sync_service: SyncService | None,
        settings: SyncSettings,
        state_store: SyncStateStore,
    ) -> None:
        self.sync_service = sync_service
        self.settings = settings
        self.state_store = state_store

    def is_due(self, now: datetime) -> bool:
        if not self.settings.enabled:
            return False
        try:
            target = time.fromisoformat(self.settings.local_time)
        except ValueError:
            return False
        local = now if now.tzinfo is not None else now.astimezone()
        if local.timetz().replace(tzinfo=None) < target:
            return False
        return self.state_store.load().last_success_local_date != local.date().isoformat()

    async def run_due(self, *, reason: Literal["startup", "scheduled"]) -> bool:
        if self.sync_service is None or not self.is_due(datetime.now().astimezone()):
            return False
        try:
            await self.sync_service.sync(
                statuses=cast(list[MarkStatus], list(self.settings.statuses)),
                include_doulists=self.settings.include_doulists,
                force=False,
                reason=reason,
            )
        except (DoubanError, OSError, ValueError):
            return False
        return True

    async def run(self) -> None:
        await asyncio.sleep(self.settings.startup_delay_seconds)
        await self.run_due(reason="startup")
        while True:
            await asyncio.sleep(60)
            await self.run_due(reason="scheduled")
