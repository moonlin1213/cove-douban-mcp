"""Durable synchronization bookkeeping without account secrets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from filelock import FileLock
from pydantic import Field

from cove_douban_mcp.domain.models import PublicModel
from cove_douban_mcp.storage.atomic_json import atomic_write_json, read_json


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
        return SyncState.model_validate(read_json(self.path, default={}))

    def save(self, state: SyncState) -> None:
        with self._lock:
            atomic_write_json(self.path, state.model_dump(mode="json"))

