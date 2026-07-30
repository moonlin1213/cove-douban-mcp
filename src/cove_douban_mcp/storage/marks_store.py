"""Durable, non-shrinking movie-mark baseline."""

from __future__ import annotations

from pathlib import Path

from filelock import FileLock
from pydantic import Field

from cove_douban_mcp.domain.merge import merge_mark_items
from cove_douban_mcp.domain.models import MovieMark, PublicModel
from cove_douban_mcp.storage.atomic_json import atomic_write_json, read_json


class MarksSnapshot(PublicModel):
    version: int = 1
    statuses: dict[str, list[MovieMark]] = Field(default_factory=dict)
    updated_at: str = ""

    def ids(self, status: str) -> set[str]:
        return {
            item.movie_id
            for item in self.statuses.get(status, [])
            if item.movie_id.strip()
        }


class MarksStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = FileLock(f"{path}.lock")

    def load(self) -> MarksSnapshot:
        value = read_json(self.path, default={})
        return MarksSnapshot.model_validate(value)

    def merge_status(self, status: str, items: list[MovieMark]) -> MarksSnapshot:
        return self.save_protected(MarksSnapshot(statuses={status: items}))

    def save_protected(self, incoming: MarksSnapshot) -> MarksSnapshot:
        with self._lock:
            current = self.load()
            statuses = {name: list(items) for name, items in current.statuses.items()}
            for status, latest in incoming.statuses.items():
                statuses[status] = merge_mark_items(statuses.get(status, []), latest)
            snapshot = MarksSnapshot(
                statuses=statuses,
                updated_at=incoming.updated_at or current.updated_at,
            )
            atomic_write_json(self.path, snapshot.model_dump(mode="json"))
            return snapshot
