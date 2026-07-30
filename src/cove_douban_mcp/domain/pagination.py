"""Shared pagination rules for all list-producing tools."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from cove_douban_mcp.domain.errors import DoubanError
from cove_douban_mcp.domain.models import Pagination

T = TypeVar("T")


def paginate(
    items: Sequence[T],
    *,
    offset: int = 0,
    limit: int = 30,
) -> tuple[list[T], Pagination]:
    if offset < 0 or not 1 <= limit <= 200:
        raise DoubanError(
            "invalid_argument",
            "offset must be non-negative and limit must be between 1 and 200",
            "Use offset >= 0 and 1 <= limit <= 200.",
        )
    page = list(items[offset : offset + limit])
    return page, Pagination(
        total=len(items),
        offset=offset,
        limit=limit,
        returned=len(page),
    )
