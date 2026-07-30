"""Bounded atomic TTL cache for successful provider queries."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from filelock import FileLock

from cove_douban_mcp.storage.atomic_json import atomic_write_json, read_json


class QueryCache:
    def __init__(
        self,
        path: Path,
        *,
        ttl_seconds: int = 21_600,
        max_entries: int = 80,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if ttl_seconds < 1 or max_entries < 1:
            raise ValueError("cache bounds must be positive")
        self.path = path
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.clock = clock
        self._lock = FileLock(f"{path}.lock")

    @staticmethod
    def make_key(operation: str, parameters: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            {"operation": operation, "parameters": parameters},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return hashlib.sha256(canonical).hexdigest()

    def _load(self) -> dict[str, dict[str, Any]]:
        document = read_json(self.path, default={"entries": {}})
        entries = document.get("entries", {})
        return entries if isinstance(entries, dict) else {}

    def _live_entries(self, entries: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        now = self.clock()
        return {
            key: entry
            for key, entry in entries.items()
            if now - float(entry.get("created_at", 0)) <= self.ttl_seconds
        }

    def _save(self, entries: dict[str, dict[str, Any]]) -> None:
        ordered = sorted(entries.items(), key=lambda item: float(item[1]["created_at"]))
        bounded = dict(ordered[-self.max_entries :])
        atomic_write_json(self.path, {"version": 1, "entries": bounded})

    def get(self, key: str) -> Any | None:
        with self._lock:
            entries = self._load()
            live = self._live_entries(entries)
            if live != entries:
                self._save(live)
            entry = live.get(key)
            return None if entry is None else entry.get("value")

    def put(self, key: str, value: Any, *, created_at: float | None = None) -> None:
        with self._lock:
            entries = self._live_entries(self._load())
            entries[key] = {
                "created_at": self.clock() if created_at is None else created_at,
                "value": value,
            }
            self._save(entries)

    def keys(self) -> list[str]:
        with self._lock:
            entries = self._live_entries(self._load())
            self._save(entries)
            return [
                key
                for key, _entry in sorted(
                    entries.items(),
                    key=lambda item: float(item[1]["created_at"]),
                )
            ]

