import pytest
from pydantic import ValidationError

from cove_douban_mcp.domain.models import (
    MovieMark,
    Pagination,
    SourceFreshness,
    ToolEnvelope,
)


def test_pagination_exposes_terminal_state() -> None:
    page = Pagination(total=42, offset=30, limit=30, returned=12)

    assert page.has_more is False
    assert page.next_offset is None


def test_pagination_exposes_next_offset() -> None:
    page = Pagination(total=61, offset=0, limit=30, returned=30)

    assert page.has_more is True
    assert page.next_offset == 30


def test_movie_mark_rejects_empty_identity() -> None:
    with pytest.raises(ValidationError):
        MovieMark(title="", movie_id="", url="")


def test_movie_mark_accepts_title_as_fallback_identity() -> None:
    mark = MovieMark(title="示例影片")

    assert mark.title == "示例影片"


def test_tool_envelope_serializes_without_private_runtime_details() -> None:
    envelope = ToolEnvelope(
        data={"items": []},
        source="cache",
        freshness=SourceFreshness(stale=False),
    )

    assert envelope.model_dump(exclude_none=True) == {
        "ok": True,
        "data": {"items": []},
        "source": "cache",
        "freshness": {"stale": False},
    }
