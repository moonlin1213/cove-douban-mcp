"""Scoped, expiring server-side storage for complete normalized results."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from filelock import FileLock
from pydantic import Field

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import Pagination, PublicModel
from cove_douban_mcp.domain.pagination import paginate
from cove_douban_mcp.domain.result_refs import new_opaque_ref
from cove_douban_mcp.storage.atomic_json import atomic_write_json, read_json

_VALID_REF = re.compile(r"^[A-Za-z0-9_-]{43,128}$")
_IDENTITY_FIELDS = (
    "movie_id",
    "subject_id",
    "review_id",
    "doulist_id",
    "item_id",
    "id",
    "url",
)


class WorkingPage(PublicModel):
    result_ref: str
    items: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    pagination: Pagination


class WorkingCache:
    def __init__(
        self,
        root: Path,
        *,
        ttl_seconds: int = 86_400,
        max_refs_per_scope: int = 16,
        max_bytes_per_ref: int = 8_388_608,
        max_total_bytes_per_scope: int = 67_108_864,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if min(
            ttl_seconds,
            max_refs_per_scope,
            max_bytes_per_ref,
            max_total_bytes_per_scope,
        ) < 1:
            raise ValueError("working-cache bounds must be positive")
        self.root = root
        self.ttl_seconds = ttl_seconds
        self.max_refs_per_scope = max_refs_per_scope
        self.max_bytes_per_ref = max_bytes_per_ref
        self.max_total_bytes_per_scope = max_total_bytes_per_scope
        self.clock = clock

    def _scope_dir(self, scope: str) -> Path:
        digest = hashlib.sha256(scope.encode()).hexdigest()
        return self.root / digest

    def _path(self, scope: str, result_ref: str) -> Path:
        if not _VALID_REF.fullmatch(result_ref):
            raise self._expired()
        return self._scope_dir(scope) / f"{result_ref}.json"

    @staticmethod
    def _expired() -> DoubanError:
        return DoubanError(
            "result_expired",
            "the working result is unavailable or has expired",
            "Run the source query again to create a new result reference.",
        )

    @staticmethod
    def _normalize_item(item: Any) -> Any:
        model_dump = getattr(item, "model_dump", None)
        return model_dump(mode="json") if callable(model_dump) else item

    @classmethod
    def _deduplicate(cls, items: Sequence[Any]) -> list[Any]:
        seen: set[str] = set()
        result: list[Any] = []
        for original in items:
            item = cls._normalize_item(original)
            identity = ""
            if isinstance(item, Mapping):
                for field in _IDENTITY_FIELDS:
                    value = item.get(field)
                    if value not in (None, ""):
                        identity = f"{field}:{value}"
                        break
            if identity and identity in seen:
                continue
            if identity:
                seen.add(identity)
            result.append(item)
        return result

    def _read_document(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise self._expired()
        document = read_json(path, default={})
        created_at = float(document.get("created_at", 0))
        if self.clock() - created_at > self.ttl_seconds:
            path.unlink(missing_ok=True)
            raise self._expired()
        return cast(dict[str, Any], document)

    def _cleanup(self, scope_dir: Path) -> None:
        entries: list[tuple[float, Path, int]] = []
        for path in scope_dir.glob("*.json"):
            try:
                document = read_json(path, default={})
                created_at = float(document.get("created_at", 0))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                path.unlink(missing_ok=True)
                continue
            if self.clock() - created_at > self.ttl_seconds:
                path.unlink(missing_ok=True)
                continue
            entries.append((created_at, path, path.stat().st_size))

        entries.sort(key=lambda entry: entry[0])
        while len(entries) > self.max_refs_per_scope:
            _created, path, _size = entries.pop(0)
            path.unlink(missing_ok=True)
        total = sum(entry[2] for entry in entries)
        while entries and total > self.max_total_bytes_per_scope:
            _created, path, size = entries.pop(0)
            path.unlink(missing_ok=True)
            total -= size

    def put(
        self,
        scope: str,
        items: Sequence[Any],
        metadata: Mapping[str, Any] | None = None,
        *,
        created_at: float | None = None,
    ) -> str:
        result_ref = new_opaque_ref()
        scope_dir = self._scope_dir(scope)
        scope_dir.mkdir(parents=True, exist_ok=True)
        normalized = self._deduplicate(items)
        document = {
            "version": 1,
            "result_ref": result_ref,
            "created_at": self.clock() if created_at is None else created_at,
            "metadata": dict(metadata or {}),
            "items": normalized,
        }
        serialized = json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        if len(serialized) > self.max_bytes_per_ref:
            raise DoubanError(
                "result_too_large",
                "the normalized result exceeds the local working-cache limit",
                "Narrow the source query and retry.",
            )

        with FileLock(scope_dir / ".scope.lock"):
            atomic_write_json(scope_dir / f"{result_ref}.json", document)
            self._cleanup(scope_dir)
        return result_ref

    def read(
        self,
        scope: str,
        result_ref: str,
        *,
        page: int = 1,
        page_size: int = 30,
    ) -> WorkingPage:
        if page < 1:
            raise DoubanError("invalid_argument", "page must be at least 1")
        scope_dir = self._scope_dir(scope)
        with FileLock(scope_dir / ".scope.lock"):
            document = self._read_document(self._path(scope, result_ref))
        items, pagination = paginate(
            document.get("items", []),
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return WorkingPage(
            result_ref=result_ref,
            items=items,
            metadata=document.get("metadata", {}),
            pagination=pagination,
        )

    def load_complete(self, scope: str, result_ref: str) -> list[Any]:
        scope_dir = self._scope_dir(scope)
        with FileLock(scope_dir / ".scope.lock"):
            document = self._read_document(self._path(scope, result_ref))
        return list(document.get("items", []))
