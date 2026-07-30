"""Safe local capability and cache status."""

from __future__ import annotations

from cove_douban_mcp.config import Settings
from cove_douban_mcp.domain.models import ToolEnvelope
from cove_douban_mcp.storage.marks_store import MarksStore
from cove_douban_mcp.storage.sync_state import SyncStateStore


class StatusService:
    def __init__(
        self,
        settings: Settings,
        marks_store: MarksStore,
        sync_state_store: SyncStateStore,
    ) -> None:
        self.settings = settings
        self.marks_store = marks_store
        self.sync_state_store = sync_state_store

    async def status(self) -> ToolEnvelope:
        snapshot = self.marks_store.load()
        sync = self.sync_state_store.load()
        return ToolEnvelope(
            data={
                "douban_access": "read_only",
                "cache": {
                    "mark_counts": {
                        status: len(items) for status, items in snapshot.statuses.items()
                    }
                },
                "sync": {
                    "enabled": self.settings.sync.enabled,
                    "running": sync.running,
                    "last_success_at": sync.last_success_at,
                },
                "export": {
                    "enabled": self.settings.export.enabled,
                    "policy": self.settings.export.policy.value,
                },
                "http": {
                    "loopback_only": True,
                    "authentication_required": True,
                },
            },
            source="local",
        )

