"""Deterministic filtering for the durable movie-mark baseline."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from cove_douban_mcp.domain.models import MovieMark

COUNTRY_ALIASES = {
    "大陆": "中国大陆",
    "国产": "中国大陆",
    "中国": "中国大陆",
    "香港": "中国香港",
    "港片": "中国香港",
    "台湾": "中国台湾",
    "台片": "中国台湾",
}

_TERM_SEPARATOR = re.compile(r"(?:\s*(?:,|，|、|;|；|/|\||或)\s*)+")  # noqa: RUF001


@dataclass(frozen=True, slots=True)
class MarkFilters:
    query: str = ""
    genre: str = ""
    country: str = ""
    director: str = ""
    cast: str = ""
    year_from: int | None = None
    year_to: int | None = None
    exclude: str | Sequence[str] = ""


def _clean_terms(parts: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for part in parts:
        value = part.strip()
        if value and value not in seen:
            seen.add(value)
            cleaned.append(value)
    return tuple(cleaned)


def normalize_country_terms(value: str) -> tuple[str, ...]:
    """Split country filters and expand only exact aliases.

    Exact matching after tokenization prevents ``香港`` from accidentally
    turning the already-canonical ``中国香港`` into a malformed value.
    """

    if not value.strip():
        return ()
    raw_terms = _clean_terms(_TERM_SEPARATOR.split(value))
    return _clean_terms([COUNTRY_ALIASES.get(term, term) for term in raw_terms])


def parse_exclude_terms(value: str | Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        return _clean_terms(_TERM_SEPARATOR.split(value))
    return _clean_terms(value)


def _text(mark: MovieMark) -> str:
    values = [
        mark.movie_id,
        mark.title,
        mark.url,
        mark.comment,
        str(mark.year or ""),
        *mark.genres,
        *mark.countries,
        *mark.directors,
        *mark.casts,
    ]
    return "\n".join(values).casefold()


def _contains(value: str, term: str) -> bool:
    return term.casefold() in value.casefold()


def filter_movie_marks(
    items: Sequence[MovieMark],
    filters: MarkFilters,
) -> list[MovieMark]:
    """Filter in a stable order while preserving source ordering."""

    excluded = tuple(term.casefold() for term in parse_exclude_terms(filters.exclude))
    requested_countries = normalize_country_terms(filters.country)
    result: list[MovieMark] = []

    for item in items:
        searchable = _text(item)
        if excluded and any(term in searchable for term in excluded):
            continue
        if filters.query and filters.query.casefold() not in searchable:
            continue
        if filters.genre and not any(_contains(genre, filters.genre) for genre in item.genres):
            continue
        if requested_countries:
            countries = {
                normalized
                for country in item.countries
                for normalized in normalize_country_terms(country)
            }
            if not countries.intersection(requested_countries):
                continue
        if filters.director and not any(
            _contains(director, filters.director) for director in item.directors
        ):
            continue
        if filters.cast and not any(_contains(cast, filters.cast) for cast in item.casts):
            continue
        if filters.year_from is not None and (item.year is None or item.year < filters.year_from):
            continue
        if filters.year_to is not None and (item.year is None or item.year > filters.year_to):
            continue
        result.append(item)

    return result
