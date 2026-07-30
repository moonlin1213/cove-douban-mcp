"""Normalized public data models shared by every transport."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PublicModel(BaseModel):
    """Base model with deterministic, forward-compatible serialization."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class SourceFreshness(PublicModel):
    stale: bool = False
    fetched_at: datetime | None = None
    cache_age_seconds: float | None = Field(default=None, ge=0)


class Pagination(PublicModel):
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=200)
    returned: int = Field(ge=0)

    @property
    def has_more(self) -> bool:
        return self.offset + self.returned < self.total

    @property
    def next_offset(self) -> int | None:
        return self.offset + self.returned if self.has_more else None


class ToolError(PublicModel):
    code: str
    message: str
    action: str = ""


class ToolEnvelope(PublicModel):
    ok: bool = True
    data: Any = None
    source: str | None = None
    freshness: SourceFreshness | None = None
    pagination: Pagination | None = None
    result_ref: str | None = None
    warning: ToolError | None = None
    error: ToolError | None = None


class MovieMark(PublicModel):
    movie_id: str = ""
    title: str = ""
    url: str = ""
    status: Literal["wish", "collect", "do"] | None = None
    rating: float | None = Field(default=None, ge=0, le=10)
    marked_at: str = ""
    comment: str = ""
    year: int | None = Field(default=None, ge=1800, le=3000)
    cover_url: str = ""
    genres: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    directors: list[str] = Field(default_factory=list)
    casts: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_identity(self) -> MovieMark:
        if not any(value.strip() for value in (self.movie_id, self.title, self.url)):
            raise ValueError("a movie mark requires movie_id, url, or title")
        return self


class SearchResult(PublicModel):
    subject_id: str = ""
    title: str
    url: str = ""
    media_type: str = ""
    year: int | None = None
    rating: float | None = None
    cover_url: str = ""


class Subject(PublicModel):
    subject_id: str = ""
    title: str
    url: str = ""
    media_type: str = ""
    year: int | None = None
    rating: float | None = None
    rating_count: int | None = None
    summary: str = ""
    genres: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    directors: list[str] = Field(default_factory=list)
    casts: list[str] = Field(default_factory=list)


class Review(PublicModel):
    review_id: str = ""
    subject_id: str = ""
    title: str = ""
    author: str = ""
    rating: float | None = None
    created_at: str = ""
    summary: str = ""
    url: str = ""


class Doulist(PublicModel):
    doulist_id: str = ""
    title: str
    url: str = ""
    item_count: int | None = None
    updated_at: str = ""


class DoulistItem(PublicModel):
    item_id: str = ""
    subject_id: str = ""
    title: str
    url: str = ""
    media_type: str = ""
    year: int | None = None
    rating: float | None = None
    note: str = ""
