"""Identity and non-shrinking merge rules for movie marks."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from cove_douban_mcp.domain.models import MovieMark

_WHITESPACE = re.compile(r"\s+")


def mark_identity(mark: MovieMark) -> str:
    if mark.movie_id.strip():
        return f"id:{mark.movie_id.strip()}"
    if mark.url.strip():
        return f"url:{mark.url.strip()}"
    normalized_title = _WHITESPACE.sub(" ", mark.title.strip()).casefold()
    return f"title:{normalized_title}"


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _enrich(existing: MovieMark, latest: MovieMark) -> MovieMark:
    merged = existing.model_dump()
    for name, value in latest.model_dump().items():
        if _has_value(value):
            merged[name] = value
    return MovieMark.model_validate(merged)


def merge_mark_items(
    existing: Sequence[MovieMark],
    latest: Sequence[MovieMark],
) -> list[MovieMark]:
    """Enrich known rows and append new rows without removing old history."""

    merged = list(existing)
    positions = {mark_identity(item): index for index, item in enumerate(merged)}
    for item in latest:
        identity = mark_identity(item)
        position = positions.get(identity)
        if position is None:
            positions[identity] = len(merged)
            merged.append(item)
        else:
            merged[position] = _enrich(merged[position], item)
    return merged

