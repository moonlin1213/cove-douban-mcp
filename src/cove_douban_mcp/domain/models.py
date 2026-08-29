"""Normalized public data models shared by every transport."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


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
    movie_id: str = Field(default="", validation_alias=AliasChoices("movie_id", "movieId"))
    title: str = ""
    url: str = ""
    status: Literal["wish", "collect", "do"] | None = Field(
        default=None,
        validation_alias=AliasChoices("status", "myStatus"),
    )
    rating: float | None = Field(
        default=None,
        ge=0,
        le=10,
        validation_alias=AliasChoices("rating", "myRating"),
    )
    marked_at: str = Field(
        default="",
        validation_alias=AliasChoices("marked_at", "myDate"),
    )
    comment: str = Field(
        default="",
        validation_alias=AliasChoices("comment", "myComment"),
    )
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
    subject_id: str = Field(
        default="",
        validation_alias=AliasChoices("subject_id", "subjectId", "id"),
    )
    title: str
    url: str = ""
    media_type: str = Field(
        default="",
        validation_alias=AliasChoices("media_type", "mediaType", "type"),
    )
    year: int | None = None
    rating: float | None = None
    cover_url: str = Field(
        default="",
        validation_alias=AliasChoices("cover_url", "coverUrl", "cover"),
    )
    abstract: str = ""


class ChartItem(PublicModel):
    rank: int = Field(ge=1)
    subject_id: str = Field(
        default="",
        validation_alias=AliasChoices("subject_id", "subjectId", "id"),
    )
    title: str
    url: str = ""
    rating: float | None = Field(default=None, ge=0, le=10)
    rating_count: int | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("rating_count", "ratingCount", "votes"),
    )
    year: int | None = Field(default=None, ge=1800, le=3000)
    summary: str = ""
    trend: str = ""
    chart_note: str = Field(
        default="",
        validation_alias=AliasChoices("chart_note", "chartNote"),
    )


class Subject(PublicModel):
    subject_id: str = Field(
        default="",
        validation_alias=AliasChoices("subject_id", "subjectId", "id"),
    )
    title: str
    url: str = ""
    media_type: str = Field(
        default="",
        validation_alias=AliasChoices("media_type", "mediaType", "type"),
    )
    year: int | None = None
    rating: float | None = None
    rating_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("rating_count", "ratingCount"),
    )
    summary: str = ""
    genres: list[str] = Field(default_factory=list)
    countries: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("countries", "country"),
    )
    directors: list[str] = Field(default_factory=list)
    casts: list[str] = Field(default_factory=list)


class Review(PublicModel):
    review_id: str = Field(
        default="",
        validation_alias=AliasChoices("review_id", "reviewId"),
    )
    subject_id: str = Field(
        default="",
        validation_alias=AliasChoices("subject_id", "subjectId", "movieId"),
    )
    title: str = ""
    author: str = ""
    rating: float | None = Field(
        default=None,
        validation_alias=AliasChoices("rating", "myRating"),
    )
    created_at: str = Field(
        default="",
        validation_alias=AliasChoices("created_at", "createdAt"),
    )
    summary: str = ""
    content: str = ""
    movie_title: str = Field(
        default="",
        validation_alias=AliasChoices("movie_title", "movieTitle"),
    )
    votes: int | None = None
    url: str = ""


class Doulist(PublicModel):
    doulist_id: str = Field(
        default="",
        validation_alias=AliasChoices("doulist_id", "doulistId", "id"),
    )
    title: str
    url: str = ""
    item_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("item_count", "itemCount", "count"),
    )
    updated_at: str = Field(
        default="",
        validation_alias=AliasChoices("updated_at", "updatedAt"),
    )
    kind: str = "all"
    description: str = ""


class DoulistItem(PublicModel):
    item_id: str = Field(
        default="",
        validation_alias=AliasChoices("item_id", "itemId"),
    )
    subject_id: str = Field(
        default="",
        validation_alias=AliasChoices("subject_id", "subjectId"),
    )
    title: str
    url: str = ""
    media_type: str = Field(
        default="",
        validation_alias=AliasChoices("media_type", "mediaType", "type"),
    )
    year: int | None = None
    rating: float | None = None
    note: str = ""
    abstract: str = ""
