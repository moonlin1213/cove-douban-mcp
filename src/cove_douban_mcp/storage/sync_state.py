"""Durable synchronization bookkeeping without account secrets."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from filelock import FileLock
from pydantic import Field

from cove_douban_mcp.domain.models import PublicModel
from cove_douban_mcp.storage.atomic_json import atomic_write_json, read_json

RUNNING_STATE_TTL = timedelta(hours=1)


class SyncState(PublicModel):
    version: int = 1
    last_checked_at: str = ""
    last_success_at: str = ""
    last_success_local_date: str = ""
    reason: str = ""
    running: bool = False
    statuses: dict[str, dict[str, Any]] = Field(default_factory=dict)
    last_error: str = ""
    plugin_schema_version: int = 1
    cache_schema_version: int = 1


class SyncStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = FileLock(f"{path}.lock")

    def load(self) -> SyncState:
        state = SyncState.model_validate(read_json(self.path, default={}))
        if not state.running:
            return state
        try:
            checked_at = datetime.fromisoformat(state.last_checked_at)
            if checked_at.tzinfo is None:
                checked_at = checked_at.astimezone()
            abandoned = datetime.now().astimezone() - checked_at > RUNNING_STATE_TTL
        except ValueError:
            abandoned = True
        if not abandoned:
            return state
        return state.model_copy(
            update={
                "running": False,
                "last_error": "previous synchronization was interrupted",
            }
        )

    def save(self, state: SyncState) -> None:
        with self._lock:
            atomic_write_json(self.path, state.model_dump(mode="json"))
